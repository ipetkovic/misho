from core.sportbooking.domain.internal_job import RefreshUserTokenJob
from core.sportbooking.service.session_token_fetch_service import SessionTokenFetchService


class RefreshUserTokenJobExecutor:
    """
    Job executor for refreshing user tokens.
    This class is responsible for executing the job that refreshes user tokens.
    """

    def __init__(self, session_token_fetch_service: SessionTokenFetchService):
        self._token_fetch_service = session_token_fetch_service

    def execute(self, job: RefreshUserTokenJob):
        """
        Execute the job to refresh user tokens.
        """
        self._token_fetch_service.refresh_token(job.user_id)
