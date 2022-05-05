from app import create_app_flask, db, cli
import os

#app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app = create_app_flask()
cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

