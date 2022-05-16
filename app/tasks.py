from celery import current_task
from flask import flash
from app import celery, db
from app.models import Task, JasperAccount, JasperCredential, User
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
def new_api_connection(username, api_key, resource_url, current_user_id):
    response = rest.echo(username,api_key,resource_url)
    if response[0] == "error":
        flash("API Connection Error")
    elif response[0] == "data":
        user = User.query.filter_by(id=current_user_id).first()
        jasper_credential = JasperCredential.query.filter_by(api_key=api_key, username=username).first()
        if jasper_credential is None:
            jasper_credential = JasperCredential(username=username, api_key=api_key, users=user)
        if JasperAccount.query.filter_by(resource_url=resource_url).first() is None:
            jasper_credential.jasper_accounts.append(JasperAccount(resource_url=resource_url))
        db.session.add(jasper_credential)
        db.session.commit()
    finish_task()
