import json
from typing import Literal, Union
import pydantic
from pydantic_core import ErrorDetails


class Unauthorized(pydantic.BaseModel):
    error_type: Literal["unauthorized"] = "unauthorized"
    error: str


class BadRequest(pydantic.BaseModel):
    error_type: Literal["bad_request"] = "bad_request"
    error: str


class ValidationErrorResponse(pydantic.BaseModel):
    error_type: Literal["validation_error"] = "validation_error"
    errors: list[ErrorDetails]


class NotFound(pydantic.BaseModel):
    error_type: Literal["not_found"] = "not_found"
    error: str


class InternalError(pydantic.BaseModel):
    error_type: Literal["internal_error"] = "internal_error"
    error: str


type ErrorType = Union[BadRequest,
                       ValidationErrorResponse, NotFound, InternalError, Unauthorized]


class Error(pydantic.RootModel[ErrorType]):
    pass

    @classmethod
    def from_json(cls, raw_json: str) -> 'Error':
        parsed = json.loads(raw_json)
        return pydantic.TypeAdapter(cls).validate_python(parsed)
