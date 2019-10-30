from flask_wtf import FlaskForm
import wtforms as f
from wtforms.validators import DataRequired, ValidationError, Length


class LoginForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired()])
    display = ['email', 'password']


class UserForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired()])
    firstname = f.StringField('firstname', validators=[DataRequired()])
    lastname = f.StringField('lastname', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired()])
    dateofbirth = f.DateField('dateofbirth', format='%d/%m/%Y')
    display = ['email', 'firstname', 'lastname', 'password', 'dateofbirth']


class StoryForm(FlaskForm):
    text = f.TextAreaField('text', validators=[DataRequired(), Length(min=1, max=1000, message='Your story is too long (max 1000 characters)')])  # TODO: Add check on length (1000 chrs)
    display = ['text']

