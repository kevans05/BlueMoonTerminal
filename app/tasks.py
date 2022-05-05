# import app
#
#
# @app.celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(1, make_file.s(), name='add every 60.0')
#
#
# @app.celery.task
# def make_file():
#     print("your mom")
#     app.logger.info("FUCK")
import app
from . import celery

@celery.task
def my_background_task():
    # some long running task here
    app.logger.info("X")