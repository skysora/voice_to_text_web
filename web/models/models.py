
from flask_login import UserMixin
from web.database import db
from web.login_manager import login_manager
from datetime import datetime
import pytz
from enum import Enum

@login_manager.user_loader
def user_loader(id):
    user = User.query.get(int(id))
    return user


class UserRoleEnum(Enum):
    ADMIN = "admin"
    NORMAL = "normal"

class User(db.Model, UserMixin):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)  # Remove unique=True
    files = db.relationship('File', backref='author', lazy=True)  # Fixed backref
    permissions = db.Column(db.Enum(UserRoleEnum), nullable=False, server_default="NORMAL")
    
    def __repr__(self):
        return '<User %r>' % self.username
    
class File(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    #origin singal path
    singal_file_path = db.Column(db.String(20),default=None)
    #submit file path 
    submit_text_file_path = db.Column(db.String(30),default=None)
    #singal identity result path
    origin_text_file_path = db.Column(db.String(30),default=None)
    #singal identity process path
    process_speech_file_path = db.Column(db.String(30),default=None)
    # edit text result path
    modified_text_file_path = db.Column(db.String(30),default=None)
    #emotion identity result path
    origin_emotion_file_path = db.Column(db.String(30),default=None)
    
    timestamp = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Asia/Taipei')))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False,default=None)

    def __repr__(self):
        return '<File %r>' % self.title

    