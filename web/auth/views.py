from flask import Blueprint,redirect, url_for,render_template,flash,session
from flask_login import login_user,login_required,current_user,logout_user
from .forms import RegisterForm,LoginForm
from web.models.models import User
from web.database import db  # Adjust the import path accordingly
from . import bctrypt

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route("/")
@login_required
def init():
    return redirect(url_for('view.azure'))


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('view.azure'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        user = User.query.filter_by(username=username).first()
        if user and bctrypt.check_password_hash(user.password,password):
            # User exists and password matched
            login_user(user,remember=remember)
            flash('Login success',category="info")
            return redirect(url_for('auth.init'))
        flash('User not exists or password not match',category='danger')
    return render_template('sign-in.html',form=form)



@auth_blueprint.route("/register",methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('view.azure'))
    form = RegisterForm()
        
        
    if form.validate_on_submit(): 
        username = form.username.data
        email = form.email.data
        password = bctrypt.generate_password_hash(form.password.data)
        user = User(username=username,password=password,email=email)
        db.session.add(user)
        db.session.commit()
        flash("Congrates registeration success",category="success")
        return  redirect(url_for('auth.login'))
    
    return render_template('sign-up.html',form=form)

@auth_blueprint.route("/logout",methods=['GET','POST'])
def logout():
    logout_user()
    session.pop('_flashes', None)
    flash('Logged out successfully', category='info')
    return redirect(url_for('auth.init'))
            
        