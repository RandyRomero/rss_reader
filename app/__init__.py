import logging
from flask import Flask
from .config import Config
from logging.config import dictConfig


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(levelname)s %(asctime)s %(module)s LINE %(lineno)d: %(message)s',
        'datefmt': '%H:%M:%S'
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__)
app.config.from_object(Config)
app.static_folder = 'static'


from app import routes
