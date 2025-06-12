from aiohttp import web

from core.sportbooking.repository.user import UserRepository


class AuthMiddleware:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    @web.middleware
    async def middleware(self, request, handler):
        if request.path == '/signup':
            return await handler(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return web.json_response({'error': 'Unauthorized'}, status=401)

        token = auth_header[len("Bearer "):]
        token = token.strip()
        user = await self._user_repository.get_user_by_auth_token(token)

        if user is None:
            return web.json_response({'error': 'Unauthorized'}, status=401)

        request['user'] = user
        return await handler(request)
