import pydantic


class Authorization(pydantic.BaseModel):
    token: str

    def to_header(self) -> str:
        return f"Bearer {self.token}"
