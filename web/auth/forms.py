from flask_wtf import FlaskForm,RecaptchaField
from wtforms import StringField,PasswordField
from wtforms.validators import DataRequired,Length,Email,EqualTo

class RegisterForm(FlaskForm):
    
    username = StringField('Username',validators = [DataRequired(),Length(min=3,max=20)])
    email = StringField('Email',validators = [DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min=8,max=20)])
    # recaptcha = RecaptchaField()
    confirm = PasswordField('Repeat Password',validators=[DataRequired(),EqualTo('password')])