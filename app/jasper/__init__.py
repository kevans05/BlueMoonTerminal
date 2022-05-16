from flask import Blueprint

bp = Blueprint('jasper', __name__)

from app.jasper import rest
