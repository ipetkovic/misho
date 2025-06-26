import os

from misho_server.config.dev import CONFIG_DEV
from misho_server.config.model import Config
from misho_server.config.prod import CONFIG_PROD


_ENV = os.getenv('MISHO_ENVIRONMENT')

_CONFIGS = {
    'DEV': CONFIG_DEV,
    'PROD': CONFIG_PROD

}

CONFIG: Config = _CONFIGS.get(_ENV, CONFIG_DEV)
