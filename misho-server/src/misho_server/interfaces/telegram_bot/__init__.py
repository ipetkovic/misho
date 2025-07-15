

class TelegramBot:
    async def start(self) -> None:
        raise NotImplementedError()

    async def stop(self) -> None:
        raise NotImplementedError()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *_):
        await self.stop()
