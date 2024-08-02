from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
import os
import requests
import ollama

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from app import views, models

def create_admin():
    from app.models import User
    admin_username = os.environ.get('ADMIN_USERNAME') or 'admin'
    admin_password = os.environ.get('ADMIN_PASSWORD') or 'admin_password'
    existing_admin = User.query.filter_by(username=admin_username).first()
    if existing_admin:
        db.session.delete(existing_admin)
        db.session.commit()
    new_admin = User(username=admin_username)
    new_admin.set_password(admin_password)
    db.session.add(new_admin)
    db.session.commit()

def check_and_download_model():
    model_name = 'mistral'
    try:
        print(f"Checking for model {model_name}...")
        response = requests.get(f"http://localhost:11434/api/models/{model_name}")
        if response.status_code == 404:
            print(f"Downloading model {model_name} using ollama.pull...")
            ollama.pull(model_name)
            print(f"Model {model_name} downloaded successfully.")
        else:
            print(f"Model {model_name} already exists.")
    except requests.RequestException as e:
        print(f"Error checking model: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

@app.before_request
def initialize():
    if initialize in app.before_request_funcs[None]:
        app.before_request_funcs[None].remove(initialize)
        db.create_all()
        create_admin()
        check_and_download_model()
