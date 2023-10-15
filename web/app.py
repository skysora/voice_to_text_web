import os
from view.views import view_blueprint
from identifly.views import identifly_blueprint
from auth.views import auth_blueprint
from auth import db,bctrypt
from flask import Flask
from config import config,TestingConfig

app = Flask(__name__)
app.config.from_object(TestingConfig)
app.register_blueprint(view_blueprint)
app.register_blueprint(identifly_blueprint)
app.register_blueprint(auth_blueprint)


db.init_app(app)
bctrypt.init_app(app)


# with app.app_context(): 
    # db.create_all()
    # print(User.query.all())
    # admin = User(username='admin',password="admin",email='admin@example.com')
    # guest = User(username='guest',password="guest",email='guest@example.com')
    # db.session.add(admin)
    # db.session.add(guest)
    # db.session.commit()
    
if __name__ == "__main__":
    
    app.run()