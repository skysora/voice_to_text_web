from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'You must login to access this page'
login_manager.login_message_category = "info"