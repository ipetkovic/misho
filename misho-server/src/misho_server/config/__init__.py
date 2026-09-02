import os

from misho_server.config.model import Config
from misho_server.config.prod import CONFIG_PROD
from misho_server.config.test import CONFIG_TEST


_ENV = os.getenv('MISHO_ENVIRONMENT', '')

_CONFIGS = {
    'TEST': CONFIG_TEST,
    'PROD': CONFIG_PROD,
}

if _ENV not in _CONFIGS:
    # Deliberately fatal rather than defaulting. A silent fallback meant that a
    # typo, or an env var that never reached the container, ran TEST settings in
    # production -- ten-second crons against the live site, and DEBUG logs. A
    # hard failure here surfaces as a failed healthcheck and an automatic
    # rollback instead.
    raise RuntimeError(
        f"MISHO_ENVIRONMENT must be one of {sorted(_CONFIGS)}, got {_ENV!r}")

CONFIG: Config = _CONFIGS[_ENV]
