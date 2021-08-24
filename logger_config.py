LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s | %(process)d | %(levelname)s | %(filename)s | %(lineno)d | %(funcName)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)-2s %(name)28s - %(levelname)-10s %(message)s',
            'datefmt': '%H:%M:%S'
        },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'access_file_handler':{
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': 'logfiles/arc.log',
            'backupCount': 3,
            'encoding': 'utf8',
            'when': 'midnight',
            'interval': 1,
            'delay': True
        },
        'exception_file_handler':{
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': 'logfiles/ex_arc.log',
            'backupCount': 3,
            'encoding': 'utf8',
            'when': 'midnight',
            'interval': 1,
            'delay': True
        }
    },
    'loggers': {
        'arc': {
            'handlers':['access_file_handler'],
            'propagate': False,
            'level':'DEBUG'
        },
        'exception': {
            'handlers': ['exception_file_handler'],
            'level': 'ERROR',
            'propagate': False
        }
    }
}