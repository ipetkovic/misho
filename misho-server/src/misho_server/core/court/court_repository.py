from misho_server.core.court import Court


class CourtRepository:
    async def list_courts(self) -> list[Court]:
        raise NotImplementedError()
