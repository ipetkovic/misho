from misho_server.core.user import User, UserCreate
from misho_server.core.user.user_repository import UserRepository
from misho_server.service.sportbooking_service import SportbookingService


class SignUpError(Exception):
    pass


class UserAlreadyExistsError(SignUpError):
    def __init__(self, message: str = "Username already exists."):
        super().__init__(message)


class WrongSportbookingCredentialsError(SignUpError):
    def __init__(self, message: str = "Unable to login to Sportbooking with provided credentials."):
        super().__init__(message)


class SignUpService:
    def __init__(self, user_service: UserRepository, sportbooking: SportbookingService):
        self._user_service = user_service
        self._sportbooking = sportbooking

    async def sign_up(self, username: str, password: str) -> User:
        existing_user = await self._user_service.get_user_by_username(username)
        if existing_user:
            raise UserAlreadyExistsError()

        try:
            token = await self._sportbooking.login(username, password)
        except Exception as e:
            raise WrongSportbookingCredentialsError() from e

        name = await self._sportbooking.get_user_account_name(token)

        user, _ = await self._user_service.create_user(
            UserCreate(
                name=name,
                username=username,
                password=password,
            )
        )

        return user
