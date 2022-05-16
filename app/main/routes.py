from datetime import datetime

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required

from app import db
from app.models import User, JasperAccount, JasperCredential, Task
from app.main import bp
from app.tasks import new_api_connection
from app.main.forms import EditProfileForm, AddJasperAPIForm


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        if current_user is None or not current_user.check_password(form.current_password.data):
            flash('Invalid current password')
        else:
            current_user.username = form.username.data
            current_user.email = form.email.data
            if form.password.data != '':
                current_user.set_password(form.password.data)
            db.session.add(current_user)
            db.session.commit()
            flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('user.html', title='Edit Profile',
                           form=form)


@bp.route('/jasper_api', methods=['GET', 'POST'])
@login_required
def jasper_api():
    form = AddJasperAPIForm(current_user.username)
    # Need to build an importer to show credits in account, and on the top bar.
    # x = current_user.jasper_credential
    # for y in x:
    #     print(y)
    #     for q in y.jasper_accounts:
    #         print(q)
    if form.validate_on_submit():
        echo_response = new_api_connection.apply_async(kwargs={"username": form.username.data, "api_key": form.api_key.data,
                                                 "resource_url": form.resource_url.data, "current_user_id": current_user.id})
        task = Task(id=echo_response.id, name='echo-test', description="testing the users credentials",
                    user=current_user)
        db.session.add(task)
        db.session.commit()

    return render_template('jasper_api.html', title='Jasper APIs', form=form)
