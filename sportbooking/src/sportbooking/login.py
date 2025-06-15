
import pydantic


class LoginResponse(pydantic.BaseModel):
    token: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
