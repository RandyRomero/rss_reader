from flask import Flask, request
from .config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
app.static_folder = 'static'

from app import routes
