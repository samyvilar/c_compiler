__author__ = 'samyvilar'

import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(message)s',
        },
    },
    'filters': {},
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        }
    },
    'loggers': {
        'loader': {
            'level': 'WARNING',
            'handlers': ['console']
        },
        'tokenizer': {
            'level': 'WARNING',
            'handlers': ['console']
        },
        'preprocessor': {
            'level': 'WARNING',
            'handlers': ['console']
        },
        'parser': {
            'level': 'WARNING',
            'handlers': ['console']
        },
        'virtual_machine': {
            'level': 'WARNING',
            'handlers': ['console']
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
import logging