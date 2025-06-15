from typing import Iterable
from aiohttp import web

from misho_server.http.auth import AuthMiddleware
from misho_server.http.internal_error import internal_error_middleware
from misho_server.repository.jobs import JobsRepository
from aiohttp.web_routedef import AbstractRouteDef


class HttpApplication:
    def __init__(self, auth_middleware: AuthMiddleware):
        self._app = web.Application(
            middlewares=[auth_middleware.middleware, internal_error_middleware]
        )

    def add_routes(self, routes: Iterable[AbstractRouteDef]):
        self._app.add_routes(routes)
        return self

    async def start_server(self):
        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8000)
        await site.start()
