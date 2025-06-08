from core.sportbooking.repository.jobs import JobsRepository

from fastapi import FastAPI

app = FastAPI()


class Jobs:
    def __init__(self, jobs_repository: JobsRepository):
        pass

    def handle(self, request: Request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)


@app.get("/")
async def root():
    return {"message": "Hello World"}
