from celery import Celery
from celery.schedules import crontab

app = Celery()

@app.on_configure

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0 * 1.0, CheckAccount.s(), name='add every 60.0')


