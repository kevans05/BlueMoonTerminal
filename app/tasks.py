import app
from app import celery, logger

# from . import celery


# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(1, make_file.s(), name='add every 60.0')

@app.celery.make_file()
def make_file():
    print("your mom")

