# vtfree/log.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union, Any


LOG_NAME = "vtfree"
_DEFAULT_PATH = Path.home() / ".vtfree" / "vtfree.log"
_DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)


def configure(path: Union[str, Path] = _DEFAULT_PATH,
              level: int = logging.INFO,
              **extra: Any) -> None:
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    # handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3)
    # handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    # Si el fichero existe con codificación previa, lo truncamos a 0 bytes
    # (equivale a `mode="w"` en RotatingFileHandler, pero algunas versiones
    # no exponen ese argumento).
    Path(path).touch()
    Path(path).write_bytes(b"")

    handler = RotatingFileHandler(filename = path,
                                  maxBytes = 2_000_000,
                                  backupCount = 3,encoding = "utf-8",  # siempre UTF‑8
                                  )
    handler.setFormatter(logging.Formatter(fmt))
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(logging.NullHandler())
