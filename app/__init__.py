import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from celery import Celery
from config import Config

db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()

login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'

logger = logging.getLogger("pylog")
logger.setLevel(logging.DEBUG)

mail = Mail()

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, result_backend=Config.RESULT_BACKEND, include=['app.tasks'
    , 'app.tasks_beat_schedule'])


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    celery.conf.update(app.config)

    celery.conf.beat_schedule = {
        'beat_schedule_check_api_connections-every-1-minutes': {
            'task': 'app.tasks_beat_schedule.beat_schedule_check_api_connections',
            'schedule': 60.0
        },'beat_schedule_check_usage_b-every-1-minutes': {
            'task': 'app.tasks_beat_schedule.beat_schedule_check_usage_b',
            'schedule': 60.0
        },'beat_schedule_organize_sims_and_rates-every-5-minutes':{
            'task': 'app.tasks_beat_schedule.beat_schedule_organize_sims_and_rates',
            'schedule': 300.0
        },
        'beat_schedule_check_sims_connections-every-1-hour': {
            'task': 'app.tasks_beat_schedule.beat_schedule_check_sims_connections',
            'schedule': 3600.0
        },
    }

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/BlueMoonTerminal.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('BlueMoonTerminal startup')
    return app


from app import models
