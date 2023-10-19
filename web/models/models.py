
from flask_login import UserMixin
from web.database import db
from web.login_manager import login_manager
from datetime import datetime
import pytz
@login_manager.user_loader
def user_loader(id):
    user = User.query.get(int(id))
    return user


class User(db.Model, UserMixin):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)  # Remove unique=True
    files = db.relationship('File', backref='author', lazy=True)  # Fixed backref

    
    def __repr__(self):
        return '<User %r>' % self.username
    
class File(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(20), unique=True, nullable=False)
    submit_text_file_path = db.Column(db.String(30), unique=True,default=None)
    origin_text_file_path = db.Column(db.String(30), unique=True,default=None)
    modified_text_file_path = db.Column(db.String(30), unique=True,default=None)
    origin_emotion_file_path = db.Column(db.String(30), unique=True,default=None)
    timestamp = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Taipei')))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False,default=None)

    def __repr__(self):
        return '<File %r>' % self.title

    