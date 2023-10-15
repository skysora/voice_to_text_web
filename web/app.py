import os
from view.views import view_blueprint
from identifly.views import identifly_blueprint
from config.config import config
from flask import Flask, abort, render_template, request, jsonify, session, Blueprint

app = Flask(__name__)
# app = create_app('testing')
# app = create_app('development')
app.register_blueprint(view_blueprint)
app.register_blueprint(identifly_blueprint)


    
if __name__ == "__main__":
    
    app.run()