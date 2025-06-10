
import os
from core.sportbooking.config_dev import CONFIG_DEV
from core.sportbooking.config_prod import CONFIG_PROD


_ENV = os.getenv('ENV', 'MISHO_ENVIRONMENT')

_CONFIGS = {
    'DEV': CONFIG_DEV,
    'PROD': CONFIG_PROD

}

CONFIG = _CONFIGS.get(_ENV, CONFIG_DEV)
