from celery import Celery, current_task
from celery.result import AsyncResult
from config import Config
from json import loads
from requests import get

from app.models import Task

from app import celery

# celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, result_backend=Config.CELERY_RESULT_BACKEND)


def _set_task_progress(progress):
    job = current_task
    print(job)
    Task.query.filter_by(id=job.request.id).first()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')
    return


@celery.task
def test(arg):
    print(arg)


@celery.task()
def echo(username, api_key, resource_url):
    _set_task_progress(0)
    url = resource_url + '/rws/api/v1/echo/hello-world'
    my_response = get(url, auth=(username, api_key))
    if my_response:
        _set_task_progress(100)
        return "data", loads(my_response.content)
    else:
        _set_task_progress(100)
        return "error", my_response.status_code
