from app.main import bp
import app.tasks

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():

    task = app.tasks.make_file.apply_async()
    return "Hello, World!"
