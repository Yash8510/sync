"""
Configure logger
"""

import logging
from pathlib import Path
from typing import Optional


def config_logging(level: str, log_file: Optional[str] = None) -> None:
    """configure logger for using it across file"""

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    
    numeric_level = getattr(logging, level.upper())
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    handlers = [stream_handler]

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_hadler = logging.FileHandler(log_file, encoding="utf-8")
        file_hadler.setFormatter(formatter)
        handlers.append(file_hadler)
    
    logging.basicConfig(level=numeric_level, handlers=handlers)
