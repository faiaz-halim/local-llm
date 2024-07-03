from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .utils import ensure_directories, load_mistral_model

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User  # Add this line

    @login_manager.user_loader  # Add this decorator and function
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'main.login'  # Specify the login view

    from .routes import main
    app.register_blueprint(main)

    ensure_directories()
    load_mistral_model()

    return app