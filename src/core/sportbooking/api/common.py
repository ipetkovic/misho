
import pydantic
from pydantic_core import ErrorDetails
from aiohttp import web


class SuccessResult(pydantic.BaseModel):
    pass


class FailureResult(pydantic.BaseModel):
    error: str


class ValidationErrorResponse(pydantic.BaseModel):
    errors: list[ErrorDetails]


def to_json(obj: pydantic.BaseModel) -> str:
    return obj.model_dump_json(indent=2)


def from_json(body: any, cls: pydantic.BaseModel):
    try:
        return cls(**body)
    except pydantic.ValidationError as e:
        raise validation_error(e)


def validation_error(e: pydantic.ValidationError) -> web.HTTPBadRequest:
    json = to_json(ValidationErrorResponse(errors=e.errors()))
    return web.HTTPBadRequest(text=json)
