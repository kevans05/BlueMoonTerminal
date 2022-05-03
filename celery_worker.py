import os
from app import celery, create_app
from config import Config

app = create_app(Config)
app.app_context().push()