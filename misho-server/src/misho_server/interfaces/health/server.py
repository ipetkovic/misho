import logging
from typing import Awaitable, Callable

from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from misho_server.interfaces.telegram_bot import TelegramBot


class HealthServer:
    """Serves GET /healthz for the Docker HEALTHCHECK and the deploy rollout.

    The bot has no other inbound surface -- it talks to Telegram by long
    polling -- so this exists purely so that something outside the process can
    tell the difference between "running" and "working". `restart:
    unless-stopped` only reacts to the process exiting, and the failure that
    actually happens here is the opposite: the process stays up while Telegram
    polling has quietly died.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        scheduler: AsyncIOScheduler,
        telegram_bot: TelegramBot,
        port: int,
    ):
        self._engine = engine
        self._scheduler = scheduler
        self._telegram_bot = telegram_bot
        self._port = port
        self._runner: web.AppRunner | None = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_get('/healthz', self._handle)

        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        # Bound inside the container only; the GCP firewall exposes no app port.
        site = web.TCPSite(runner, '0.0.0.0', self._port)
        await site.start()

        self._runner = runner
        logging.info("Health endpoint listening on :%d/healthz", self._port)

    async def stop(self) -> None:
        if self._runner is None:
            return
        await self._runner.cleanup()
        self._runner = None

    async def _handle(self, _: web.Request) -> web.Response:
        checks = {
            'scheduler': self._check_scheduler,
            'telegram': self._check_telegram,
            'database': self._check_database,
        }

        results: dict[str, bool] = {}
        for name, check in checks.items():
            results[name] = await _safe(name, check)

        healthy = all(results.values())
        return web.json_response(
            {'status': 'ok' if healthy else 'unhealthy', 'checks': results},
            status=200 if healthy else 503,
        )

    async def _check_scheduler(self) -> bool:
        return self._scheduler.running

    async def _check_telegram(self) -> bool:
        return self._telegram_bot.is_polling()

    async def _check_database(self) -> bool:
        async with self._engine.connect() as connection:
            await connection.execute(text('SELECT 1'))
        return True


async def _safe(name: str, check: Callable[[], Awaitable[bool]]) -> bool:
    """A probe that raises is a failed probe, never a 500.

    A traceback out of the handler would make aiohttp answer 500, which the
    HEALTHCHECK reads the same as 503 -- but it would also lose which check
    broke, and that is the only thing this endpoint is for.
    """
    try:
        return await check()
    except Exception:
        logging.exception("Health check %r failed", name)
        return False
