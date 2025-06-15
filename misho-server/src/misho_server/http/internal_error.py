import logging
from aiohttp import web

from misho_api import InternalError
from misho_server.controller.common import to_json


def internal_error() -> web.HTTPInternalServerError:
    response_data = to_json(InternalError(error="Internal Server Error"))
    return web.HTTPInternalServerError(text=response_data, content_type='application/json')


@web.middleware
async def internal_error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except web.HTTPException as ex:
        raise ex
    except Exception as ex:
        logging.error(
            f"Error while processing HTTP server request", exc_info=True)
        return internal_error()
