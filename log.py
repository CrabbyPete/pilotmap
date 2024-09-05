import sys
from loguru import logger as log

fmt = "<level>{level: <6}</level>|<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>-<level>{message}</level>"
config = {
    "handlers": [
        {"sink": sys.stderr, "format": fmt},
    ],
}
log.configure(**config)