import os
from app import create_app

app = create_app()
app.app_context().push()

from app import celery

#celery -A celery_worker.celery worker -l debug -B -f celery.log
#celery -A celery_worker.celery worker -l debug -B -f celery.log