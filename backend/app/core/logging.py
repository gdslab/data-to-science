import json
import logging
import os
import sys
from functools import lru_cache
from http import HTTPStatus
from io import TextIOBase
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List

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


def get_app_json_log(record: logging.LogRecord) -> Dict:
    record_format = {
        "levelname": record.levelname,
        "type": "app",
        "module": record.module,
        "lineno": record.lineno,
        "message": record.message,
    }

    if record.exc_info:
        record_format["exc_info"] = repr(record.exc_info[:2])

    return record_format


def get_access_json_log(record: logging.LogRecord) -> Dict:
    req = ""
    res = ""
    if hasattr(record, "extra_info"):
        req = record.extra_info.get("req", "")
        res = record.extra_info.get("res", "")

    record_format = {
        "levelname": record.levelname,
        "type": "access",
        "module": record.module,
        "lineno": record.lineno,
        "message": record.message,
        "req": req,
        "res": res,
    }

    if record.exc_info:
        record_format["exc_info"] = repr(record.exc_info)

    return record_format


class CustomJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
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


def get_logger_config(nofile: bool = False) -> LoggerConfig:
    # Get the current log directory from settings
    current_logdir = Path(settings.API_LOGDIR)
    current_logfile = current_logdir / "backend.log"

    # stdout handler
    stdout_handler_format = logging.Formatter(LOGGER_FORMAT, datefmt=DATE_FORMAT)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(stdout_handler_format)
    stdout_handler.setLevel(logging.DEBUG)

    handlers: List[logging.StreamHandler[TextIOBase | Any] | logging.FileHandler] = [
        stdout_handler
    ]
    if not nofile:
        # file handler with daily rotation, keeping logs for 7 days
        output_file_handler = TimedRotatingFileHandler(
            current_logfile,
            when="midnight",  # Rotate at midnight
            interval=1,  # Every day
            backupCount=7,  # Keep 7 days of logs
            encoding="utf-8",
        )
        output_file_handler.setFormatter(CustomJsonFormatter(datefmt=DATE_FORMAT))
        output_file_handler.setLevel(logging.DEBUG)

        handlers.append(output_file_handler)

    return LoggerConfig(
        handlers=handlers,
        format="%(levelname)s: %(asctime)s \t%(message)s",
        date_format="%d-%b-%Y %H:%M:%S",
        logger_file=current_logfile,
    )


def get_http_info(request: Request, response: Response) -> Dict:
    return {
        "req": {
            "url": request.url.path,
            "query_string": request.url.query,
            "query_params": dict(request.query_params),
            "headers": {
                "host": request.headers.get("host"),
                "user-agent": request.headers.get("user-agent"),
                "accept": request.headers.get("accept"),
                "content-type": request.headers.get("content-type"),
                "content-length": request.headers.get("content-length"),
            },
            "method": request.method,
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None,
            },
        },
        "res": {
            "status_code": response.status_code,
            "status_detail": http_status_lookup.get(response.status_code),
            "headers": {
                "content-type": response.headers.get("content-type"),
                "content-length": response.headers.get("content-length"),
            },
        },
    }


def setup_logger() -> None:
    os.makedirs(API_LOGDIR, exist_ok=True)

    # Reset only the root logger handlers so third-party loggers keep theirs
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    try:
        logger_config: Any = get_logger_config()
    except PermissionError:
        logger_config = get_logger_config(nofile=True)

    logger_format = logger_config.format or ""

    logging.basicConfig(
        level=logger_config.level,
        format=logger_format,
        datefmt=logger_config.date_format,
        handlers=logger_config.handlers,
    )
