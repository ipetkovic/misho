from core.sportbooking.repository.jobs import JobsRepository

from aiohttp import web


class JobsController:
    def __init__(self, jobs_repository: JobsRepository):
        self.jobs_repository = jobs_repository

    def register_routes(self, app: web.Application):
        app.add_routes([
            web.get('/jobs', self.handle),
        ])

    async def handle(self, request):
        print("jaje")
        jobs = await self.jobs_repository.list_all()
        print(jobs)
        return web.Response(text=str(jobs))
