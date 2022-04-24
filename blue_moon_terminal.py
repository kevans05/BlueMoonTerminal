from app import create_app, db, cli
#from app.models import User
import os

#app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app = create_app()
cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

