import httpx
from core.api import Error
from core.api.job import Job, JobCreate, JobsResult
from core.client import Authorization
from core.domain.job import Status


class JobClient:
    def __init__(self, http_client: httpx.AsyncClient, url: str):
        self._http_client = http_client
        self._base_url = url

    async def list_jobs(self, authorization: Authorization, status: Status = None) -> list[Job] | Error:
        request = httpx.Request(
            method="GET",
            url=self._base_url + "/jobs",
            headers={"Authorization": authorization.to_header()},
            params={"status": status.value} if status else None
        )
        response = await self._http_client.send(request)

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return JobsResult(**response.json())


if __name__ == "__main__":
    # Example usage
    async def main():
        async with httpx.AsyncClient() as client:
            job_client = JobClient(client, "http://localhost:8000")
            jobs = await job_client.list_jobs(authorization=Authorization(token='4a7b99400983d2067a7c54f8d3cf7274'))
            print(jobs)

    import asyncio
    asyncio.run(main())
