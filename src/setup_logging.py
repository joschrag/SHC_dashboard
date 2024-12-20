import atexit
import logging
import logging.config
import logging.handlers
import pathlib
from typing import override

import yaml


def setup_logging():
    config_file = pathlib.Path.cwd() / "log_config.yaml"
    with open(config_file) as f_in:
        config = yaml.load(f_in, yaml.SafeLoader)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


class NonErrorFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO
