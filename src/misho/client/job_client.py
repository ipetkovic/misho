import httpx
from misho_api import Error
from misho_api.job import JobApi, JobCreateApi, JobListApi
from misho.client import Authorization
from misho.domain.job import Status


class JobClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http_client = http_client
        self._base_url = base_url

    async def list_jobs(self, authorization: Authorization, status: Status = None) -> list[JobApi] | Error:
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

        return JobListApi(**response.json()).jobs

    async def get_job(self, authorization: Authorization, job_id: int) -> JobApi | Error:
        request = httpx.Request(
            method="GET",
            url=self._base_url + f"/jobs/{job_id}",
            headers={"Authorization": authorization.to_header()}
        )
        response = await self._http_client.send(request)

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return JobApi(**response.json())

    async def create_job(self, authorization: Authorization, job_create: JobCreateApi) -> JobApi | Error:
        request = httpx.Request(
            method="POST",
            url=self._base_url + "/jobs",
            headers={
                "Authorization": authorization.to_header(),
                "Content-Type": "application/json"
            },
            json=job_create.model_dump(mode="json")
        )
        response = await self._http_client.send(request)

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return JobApi(**response.json())

    async def delete_job(self, authorization: Authorization, job_id: int) -> None | Error:
        request = httpx.Request(
            method="DELETE",
            url=self._base_url + f"/jobs/{job_id}",
            headers={"Authorization": authorization.to_header()}
        )
        response = await self._http_client.send(request)

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return None


# if __name__ == "__main__":
#     # Example usage
#     async def main():
#         async with httpx.AsyncClient() as client:
#             job_client = JobClient(client, "http://localhost:8000")
#             jobs = await job_client.get_job(authorization=Authorization(token='4a7b99400983d2067a7c54f8d3cf7274'), job_id=2)
#             print(jobs)

#     import asyncio
#     asyncio.run(main())
