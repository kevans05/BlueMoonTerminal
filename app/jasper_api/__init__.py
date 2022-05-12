from flask import Blueprint

bp = Blueprint('jasper_api', __name__)

from app.jasper_api import rest
