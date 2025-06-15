import os
import pydantic


class CliConfig(pydantic.BaseModel):
    host_url: str
    host_port: int
    token: str | None


MISHO_CLI_KEY = os.environ.get('MISHO_ACCESS_KEY', None)


CONFIG = CliConfig(
    host_url="http://ec2-52-57-94-53.eu-central-1.compute.amazonaws.com",
    # host_url="http://localhost",
    host_port=8000,
    token=MISHO_CLI_KEY
)
