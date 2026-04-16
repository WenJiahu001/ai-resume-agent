"""日志配置"""

import logging
import sys
from functools import lru_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@lru_cache
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
