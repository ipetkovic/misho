

class TelegramBot:
    async def start(self) -> None:
        raise NotImplementedError()

    async def stop(self) -> None:
        raise NotImplementedError()

    def is_polling(self) -> bool:
        """Whether the bot is currently consuming Telegram updates.

        Reported by /healthz. The process staying alive says nothing about
        this -- polling can stop on its own (a 409 from a second client on the
        same token, say) while everything else keeps running.
        """
        raise NotImplementedError()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *_):
        await self.stop()
