import requests
from misho_api import Error
from misho_api.job import JobApi, JobCreateApi, JobListApi, StatusApi
from misho_client import Authorization


class JobClient:
    def __init__(self, base_url: str):
        self._base_url = base_url

    def list_jobs(self, authorization: Authorization, status: StatusApi = None) -> list[JobApi] | Error:
        request = requests.Request(
            method="GET",
            url=self._base_url + "/jobs",
            headers={"Authorization": authorization.to_header()},
            params={"status": status.value} if status else None
        )

        with requests.Session() as session:
            response = session.send(request.prepare())

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return JobListApi(**response.json()).jobs

    def get_job(self, authorization: Authorization, job_id: int) -> JobApi | Error:
        request = requests.Request(
            method="GET",
            url=self._base_url + f"/jobs/{job_id}",
            headers={"Authorization": authorization.to_header()}
        )

        with requests.Session() as session:
            response = session.send(request.prepare())

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return JobApi(**response.json())

    def create_job(self, authorization: Authorization, job_create: JobCreateApi) -> JobApi | Error:
        request = requests.Request(
            method="POST",
            url=self._base_url + "/jobs",
            headers={
                "Authorization": authorization.to_header(),
                "Content-Type": "application/json"
            },
            json=job_create.model_dump(mode="json")
        )

        with requests.Session() as session:
            response = session.send(request.prepare())

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return JobApi(**response.json())

    def delete_job(self, authorization: Authorization, job_id: int) -> None | Error:
        request = requests.Request(
            method="DELETE",
            url=self._base_url + f"/jobs/{job_id}",
            headers={"Authorization": authorization.to_header()}
        )

        with requests.Session() as session:
            response = session.send(request.prepare())

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
