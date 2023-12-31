from flask import Blueprint,redirect, url_for,render_template,flash,session
from flask_login import login_user,login_required,current_user,logout_user
from .forms import RegisterForm,LoginForm
from web.models.models import User
from web.database import db  # Adjust the import path accordingly
import subprocess
from . import bctrypt
import json
from web.module.auth import *
auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route("/")
@login_required
def init():
    with open(f'{TOKEN_PATH}', 'r') as token_file:
        data = json.load(token_file)
        
        command  = f'/root/.dotnet/tools/spx config @key --set {data["voiceKey"]}'
        subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        command  = f'/root/.dotnet/tools/spx config @region --set {data["voiceLocation"]}'
        subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return redirect(url_for('view.datatable'))

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
    
    return render_template('auth/sign-up.html',form=form)

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
    return render_template('auth/sign-in.html',form=form)


@auth_blueprint.route("/logout",methods=['GET','POST'])
def logout():
    logout_user()
    session.pop('_flashes', None)
    flash('Logged out successfully', category='info')
    return redirect(url_for('auth.init'))
            
        