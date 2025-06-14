

from core.api.job import Job, JobCreate


class JobClient:
    """
    A client for managing jobs in a system.
    """

    def __init__(self, job_manager):
        """
        Initializes the JobClient with a job manager.

        :param job_manager: An instance of a job manager that handles job operations.
        """
        self.job_manager = job_manager

    def create_job(self, job_create: JobCreate) -> Job:
        return self.job_manager.create_job(job_data)
