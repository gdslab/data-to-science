import json
import logging
import os
import sys
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path
from traceback import print_exception

from fastapi import Request, Response
from pydantic import BaseModel

from app.core.config import settings


API_LOGDIR = Path(settings.API_LOGDIR)
API_LOGFILE = API_LOGDIR / "backend.log"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOGGER_FORMAT = "%(asctime)s | %(message)s"


http_status_lookup = {status.value: status.name for status in list(HTTPStatus)}


class LoggerConfig(BaseModel):
    handlers: list
    format: str | None = None
    date_format: str | None = None
    logger_file: Path | None = None
    level: int = logging.INFO


def get_app_json_log(record: logging.LogRecord):
    record_format = {
        "levelname": record.levelname,
        "type": "app",
        "module": record.module,
        "lineno": record.lineno,
        "message": record.message,
    }

    if record.exc_info:
        record_format["exc_info"] = repr(record.exc_info)

    return record_format


def get_access_json_log(record: logging.LogRecord):
    record_format = {
        "levelname": record.levelname,
        "type": "access",
        "module": record.module,
        "lineno": record.lineno,
        "message": record.message,
        "req": record.extra_info["req"],
        "res": record.extra_info["res"],
    }

    if record.exc_info:
        record_format["exc_info"] = repr(record.exc_info)

    return record_format


class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()  # Ensure message is formatted
        if hasattr(record, "extra_info"):
            return json.dumps(
                {
                    "asctime": self.formatTime(record, self.datefmt),
                    **get_access_json_log(record),
                }
            )
        else:
            return json.dumps(
                {
                    "asctime": self.formatTime(record, self.datefmt),
                    **get_app_json_log(record),
                }
            )


@lru_cache
def get_logger_config(nofile = False):  
    # stdout handler
    stdout_handler_format = logging.Formatter(LOGGER_FORMAT, datefmt=DATE_FORMAT)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(stdout_handler_format)
    stdout_handler.setLevel(logging.DEBUG)

    handlers = [stdout_handler]
    if not nofile:
        # file handler
        output_file_handler = logging.FileHandler(API_LOGFILE)
        output_file_handler.setFormatter(CustomJsonFormatter(datefmt=DATE_FORMAT))
        output_file_handler.setLevel(logging.DEBUG)

        handlers.append(output_file_handler)

    return LoggerConfig(
        handlers=handlers,
        format="%(levelname)s: %(asctime)s \t%(message)s",
        date_format="%d-%b-%Y %H:%M:%S",
        logger_file=API_LOGFILE,
    )


def get_http_info(request: Request, response: Response):
    return {
        "req": {
            "url": request.url.path,
            "headers": {
                "host": request.headers["host"],
                "user-agent": request.headers["user-agent"],
                "accept": request.headers["accept"],
            },
            "method": request.method,
        },
        "res": {
            "status_code": response.status_code,
            "status_detail": http_status_lookup.get(response.status_code),
        },
    }


def setup_logger():
    if not os.path.exists(API_LOGDIR):
        os.makedirs(API_LOGDIR)

    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    try:
        logger_config = get_logger_config()
    except PermissionError:
        logger_config = get_logger_config(nofile=True)

    logging.basicConfig(
        level=logger_config.level,
        format=logger_config.format,
        datefmt=logger_config.date_format,
        handlers=logger_config.handlers,
    )
