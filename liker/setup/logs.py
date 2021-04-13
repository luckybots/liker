import time
import logging.config

from liker.setup import constants


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


def setup_logs():
    constants.log_dir().mkdir(exist_ok=True, parents=True)
    logging_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                '()': UTCFormatter,
                'format': constants.LOG_FORMAT
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': constants.log_dir() / "log.log",
                'when': "midnight",
                'backupCount': 30,
            },
            'error': {
                'level': 'ERROR',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': constants.log_dir() / "errors.log",
                'maxBytes': 1*1024*1024,
                'backupCount': 1,
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file', 'error'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'tengine': {
                'handlers': ['console', 'file', 'error'],
                'level': 'DEBUG',
                'propagate': True,
            },
            # Mute mtprotosender logs
            'telethon': {
                'propagate': False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


setup_logs()
