from flask import Blueprint

bp = Blueprint('celery_tasks', __name__)

from app.celery_tasks import tasks

