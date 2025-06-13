import pydantic
from core.api.common import FailureResult, from_json, to_json
from core.api.user import User
from core.domain.user import UserCreate
from core.integration.sportbooking_service import SportbookingService
from core.repository.user import UserRepository
from aiohttp import request, web


class SignupRequest(pydantic.BaseModel):
    username: str
    password: str
    email: pydantic.EmailStr


class SignupResponse(pydantic.BaseModel):
    user: User
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
            error = FailureResult(
                error="Username already exists.")
            return web.json_response(status=400, body=to_json(error))

        try:
            token = await self._sportbooking.login(
                user_request.username, user_request.password)
        except Exception as e:
            error = FailureResult(
                error="Unable to login to Sportbooking with provided credentials.")
            return web.json_response(status=400, body=to_json(error))

        name = await self._sportbooking.get_user_account_name(token)

        user, app_token = await self._user_service.create_user(
            UserCreate(
                name=name,
                username=user_request.username,
                password=user_request.password,
                email=user_request.email
            )
        )

        jobs_json = to_json(SignupResponse(
            user=User(
                name=user.name,
                username=user.username,
                email=user.email,
            ),
            token=app_token.token
        ))
        return web.json_response(body=jobs_json)
