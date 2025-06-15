from aiohttp import web

from misho_api import Unauthorized
from misho_server.repository.user import UserRepository


def unauthorized_error() -> web.HTTPUnauthorized:
    error = Unauthorized(error="Unauthorized")
    print(error)
    json = error.model_dump_json(indent=2)
    return web.HTTPUnauthorized(
        text=json,
        content_type='application/json'
    )


class AuthMiddleware:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    @web.middleware
    async def middleware(self, request, handler):
        if request.path == '/signup':
            return await handler(request)

        auth_header = request.headers.get('Authorization')

        print(auth_header)

        if not auth_header or not auth_header.startswith("Bearer "):
            return unauthorized_error()

        token = auth_header[len("Bearer "):]
        token = token.strip()
        user = await self._user_repository.get_user_by_auth_token(token)

        print(user)

        if user is None:
            return unauthorized_error()

        request['user'] = user
        return await handler(request)
