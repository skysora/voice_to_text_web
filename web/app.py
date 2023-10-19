import os
from flask import Flask


from config import TestingConfig
from web.database import db
from web.login_manager import login_manager
from auth import bctrypt
from auth.views import auth_blueprint
from view.views import view_blueprint
from identify.views import identifly_blueprint


app = Flask(__name__)
app.config.from_object(TestingConfig) 
app.register_blueprint(auth_blueprint)
app.register_blueprint(view_blueprint)
app.register_blueprint(identifly_blueprint)
db.init_app(app) 
bctrypt.init_app(app)
login_manager.init_app(app)
    

def setup_database(app):
  with app.app_context():
      db.create_all()

# with app.app_context():
#   db.create_all()  
  
       
if __name__ == "__main__":
  # Because this is just a demonstration we set up the database like this.
  if not os.path.isfile(TestingConfig['SQLALCHEMY_DATABASE_URI']):
    setup_database(app)
  app.run()