
from flask_login import UserMixin
from . import db,bctrypt

# @login_manager.user_loader
# def load_user(user_id):
#     return User.get(id)


class User(db.Model,UserMixin):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120),nullable=False)
    password = db.Column(db.String(20), unique=True, nullable=False)
    
    
    def __repr__(self):
        return '<User %r>' % self.username
    
    
class LoginManager(object):
    def __init__(self, app=None, add_context_processor=True):
        #  ...中略
        if app is not None:
            self.init_app(app, add_context_processor)   