from flask import Blueprint,Flask, request, redirect, url_for,render_template,flash
from .forms import RegisterForm
# from .models import User
from . import db,bctrypt
from .models import User

auth_blueprint = Blueprint('auth', __name__, template_folder='templates')

@auth_blueprint.route("/")
def init():
    return redirect(url_for('auth.register'))


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)

        flash('Logged in successfully.')

        next = request.args.get('next')
        # url_has_allowed_host_and_scheme should check if the url is safe
        # for redirects, meaning it matches the request host.
        # See Django's url_has_allowed_host_and_scheme for an example.
        if not url_has_allowed_host_and_scheme(next, request.host):
            return abort(400)

        return redirect(next or url_for('index'))
    return render_template('sign-in.html', form=form)



@auth_blueprint.route("/register",methods=['GET','POST'])
def register():
    form = RegisterForm()
    print(User.query.all())
    
    with open("test.txt","w") as file:
        file.write(str(User.query.all()))
        
        
    if form.validate_on_submit(): 
        username = form.username.data
        email = form.email.data
        password = bctrypt.generate_password_hash(form.password.data)
        user = User(username=username,password=password,email=email)
        db.session.add(user)
        db.session.commit()
        flash("Congrates registeration success",category="success")
    
    return render_template('sign-up.html',form=form)



            
        