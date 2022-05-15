from celery import Celery
from config import Config

from json import loads
from requests import get


celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, result_backend=Config.CELERY_RESULT_BACKEND)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    return


@celery.task()
def echo(username, api_key, resource_url):
    url = 'https://' + resource_url + '/rws/api/v1/echo/hello-world'
    my_response = get(url, auth=(username, api_key))
    if my_response:
        return "data", loads(my_response.content)
    else:
        return "error", my_response.status_code
