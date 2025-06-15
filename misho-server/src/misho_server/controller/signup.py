import pydantic
from misho_server.controller.common import bad_request, from_json, success_response
from misho_api.user import UserApi
from misho_server.domain.user import UserCreate
from misho_server.service.sportbooking_service import SportbookingService
from misho_server.repository.user import UserRepository
from aiohttp import web


class SignupRequest(pydantic.BaseModel):
    username: str
    password: str
    email: pydantic.EmailStr


class SignupResponse(pydantic.BaseModel):
    user: UserApi
    token: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class SignUpController:
    def __init__(self, user_service: UserRepository, sportbooking: SportbookingService):
        self._user_service = user_service
        self._sportbooking = sportbooking

    def get_routes(self):
        return [
            web.post('/signup', self.sign_up),
        ]

    async def sign_up(self, request: web.Request) -> UserRepository:
        body = await request.json()
        json = from_json(body, SignupRequest)
        user_request = SignupRequest.model_validate(json)

        existing_user = await self._user_service.get_user_by_username(user_request.username)
        if existing_user:
            return bad_request(error="Username already exists.")

        try:
            token = await self._sportbooking.login(
                user_request.username, user_request.password)
        except Exception as e:
            return bad_request(
                "Unable to login to Sportbooking with provided credentials."
            )

        name = await self._sportbooking.get_user_account_name(token)

        user, app_token = await self._user_service.create_user(
            UserCreate(
                name=name,
                username=user_request.username,
                password=user_request.password,
                email=user_request.email
            )
        )

        response = SignupResponse(
            user=UserApi(
                name=user.name,
                username=user.username,
                email=user.email,
            ),
            token=app_token.token
        )
        return success_response(response)
