from pathlib import Path

LOGGING_CONFIGURATION = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "dry": {
            "format": "%(message)s"
        },
        "simple": {
            "format": "[%(asctime)s][%(levelname)s]: %(message)s"
        },
        "debug": {
            "format": "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s.%(funcName)s:%(lineno)s]: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "debug_file_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "debug",
            "filename": Path(".", "logs", "debug.log"),  # hardcoded :(
            "encoding": "utf8"
        },
        "info_file_handler": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": Path(".", "logs", "info.log"),  # hardcoded :(
            "encoding": "utf8"
        },
    },
    "loggers": {
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console",
            "debug_file_handler",
            "info_file_handler"
        ],
    }
}
