from app import celery

from . import celery


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print("FUCK")
    sender.add_periodic_task(20, make_file.s(), name='add every 60.0')

@celery.task()
def make_file():
    print("your mom")

