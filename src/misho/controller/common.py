
import pydantic
from aiohttp import web

from misho_api import BadRequest, NotFound, ValidationErrorResponse


def to_json(obj: pydantic.BaseModel) -> str:
    return obj.model_dump_json(indent=2)


def from_json(body: any, cls: pydantic.BaseModel):
    try:
        return cls(**body)
    except pydantic.ValidationError as e:
        raise validation_error(e)


def bad_request(message: str) -> web.HTTPBadRequest:
    json = to_json(BadRequest(error=message))
    return web.HTTPBadRequest(text=json, content_type='application/json')


def validation_error(e: pydantic.ValidationError) -> web.HTTPBadRequest:
    json = to_json(ValidationErrorResponse(errors=e.errors()))
    return web.HTTPBadRequest(text=json, content_type='application/json')


def not_found(message: str) -> web.HTTPNotFound:
    json = to_json(NotFound(error=message))
    return web.HTTPNotFound(text=json, content_type='application/json')


def success_response(data: pydantic.BaseModel) -> web.Response:
    json = to_json(data)
    return web.json_response(body=json)
