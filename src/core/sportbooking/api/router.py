from aiohttp import web

from core.sportbooking.repository.jobs import JobsRepository


class HttpApplication:
    def __init__(self, jobs_repository: JobsRepository):
        app = web.Application()
        app.add_routes([web.get('/jobs', handle),
                        web.get('/{name}', handle)])

    async def handle(self, request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)
