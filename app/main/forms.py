from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, length, URL
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password (Leave blank if no change)')
    password2 = PasswordField(
        'Repeat New Password  (Leave blank if no change)', validators=[EqualTo('password')])
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class AddJasperAPIForm(FlaskForm):
    username = StringField('Jasper username', validators=[DataRequired()])
    api_key = PasswordField('Jasper API Key for User', validators=[DataRequired(), length(min=35, max=36,)])
    resource_url = StringField('Resource URL', validators=[DataRequired(), URL(require_tld=True)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(AddJasperAPIForm, self).__init__(*args, **kwargs)
        self.original_username = original_username


class AddSIMs(FlaskForm):
    ListOfICCID = TextAreaField('Put ICCIDs seperated by a new line')
    submit = SubmitField('Submit')