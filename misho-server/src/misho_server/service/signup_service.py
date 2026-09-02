from misho_server.core.user import User, UserCreate
from misho_server.core.user.user_repository import UserRepository
from misho_server.service.sportbooking_service import SportbookingService


class SignUpError(Exception):
    pass


class WrongSportbookingCredentialsError(SignUpError):
    def __init__(self, message: str = "Unable to login to Sportbooking with provided credentials."):
        super().__init__(message)


class SignUpService:
    def __init__(self, user_service: UserRepository, sportbooking: SportbookingService):
        self._user_service = user_service
        self._sportbooking = sportbooking

    async def sign_up(self, username: str, password: str) -> User:
        """Create -- or recover -- the user behind these sportbooking credentials.

        Credentials are checked first: whether the account already exists is
        only safe to act on once the caller has proved they own it.
        """
        try:
            token = await self._sportbooking.login(username, password)
        except Exception as e:
            raise WrongSportbookingCredentialsError() from e

        existing_user = await self._user_service.get_user_by_username(username)
        if existing_user:
            # An earlier attempt got as far as creating the user and then
            # failed to link it. Hand it back so the caller can finish the job:
            # rejecting it would strand the user behind a row they can neither
            # see nor delete.
            return existing_user

        name = await self._sportbooking.get_user_account_name(token)

        user, _ = await self._user_service.create_user(
            UserCreate(
                name=name,
                username=username,
                password=password,
            )
        )

        return user
