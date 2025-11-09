import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def _current_log_path() -> str:
    return os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")

def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        fh = logging.FileHandler(_current_log_path(), encoding="utf-8")
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(pathname)s:%(lineno)d | %(funcName)s | %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        # Optional console handler
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        logger.propagate = False
    return logger

logger = get_logger()

def log_call(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            arg_preview = []
            for a in args:
                s = repr(a)
                arg_preview.append(s[:120] + ("..." if len(s) > 120 else ""))
            kw_preview = {k: (repr(v)[:120] + ("..." if len(repr(v)) > 120 else "")) for k, v in kwargs.items()}
            logger.debug(f"ENTER {fn.__name__} args={arg_preview} kwargs={kw_preview}")
            result = fn(*args, **kwargs)
            logger.debug(f"EXIT {fn.__name__} result_type={type(result).__name__}")
            return result
        except Exception as e:
            logger.exception(f"EXCEPTION in {fn.__name__}: {e}")
            raise
    return wrapper