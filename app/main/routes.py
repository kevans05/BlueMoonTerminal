from datetime import datetime

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required


from app import db
from app.models import User, JasperAccount, JasperCredential, SubscriberIdentityModule
from app.main import bp
from app.tasks import add_rate_plans, get_iccids, add_api_connections, update_iccids
from app.main.forms import EditProfileForm, AddJasperAPIForm, AddSIMs


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
    if form.validate_on_submit():
        add_api_connections.apply_async(
            kwargs={"username": form.username.data, "api_key": form.api_key.data,
                    "resource_url": form.resource_url.data, "current_user_id": current_user.id})


        add_rate_plans.apply_async(
            kwargs={"username": form.username.data, "api_key": form.api_key.data,
                    "resource_url": form.resource_url.data})

        get_iccids.apply_async(kwargs={"username": form.username.data, "api_key": form.api_key.data,
                                                         "resource_url": form.resource_url.data})

        update_iccids.apply_async(
            kwargs={"username": form.username.data, "api_key": form.api_key.data,
                    "resource_url": form.resource_url.data})
        db.session.commit()
    if current_user.number_of_jasper_credential() >= 1:
        jasper_credentials = current_user.jasper_credential
    else:
        jasper_credentials = None
    return render_template('jasper_api.html', title='Jasper APIs', form=form, available_apis=jasper_credentials)


@bp.route('/<token>/sim', methods=['GET', 'POST'])
@login_required
def subscriber_identity_module(token):
    form = AddSIMs()
    jasper_account = JasperAccount.verify_id_token(token)
    if form.validate_on_submit():
        for iccid in form.ListOfICCID.data.splitlines():
            if SubscriberIdentityModule.query.filter_by(iccid=iccid).first() is None:
                jasper_account.subscriber_identity_modules.append(SubscriberIdentityModule(iccid=iccid))
        db.session.add(jasper_account)
        db.session.commit()
    return render_template('subscriber_identity_module.html', title='Subscriber Identity Module', form=form,
                           jasper_account=jasper_account)
