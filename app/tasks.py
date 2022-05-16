from celery import current_task


from app import celery, db
from app.models import Task
from app.jasper import rest


def finish_task():
    job = current_task
    task = Task.query.filter_by(id=job.request.id).first()
    task.complete = True
    db.session.commit()


@celery.task
def add(x, y):
    z = x + y
    print(z)


@celery.task()
def new_api_connection(username, api_key, resource_url):
    rest.echo(username,api_key,resource_url)
    finish_task()
