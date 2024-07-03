import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure required directories exist
required_dirs = ['uploads', 'models', 'backups', 'instance']
for dir in required_dirs:
    os.makedirs(os.path.join(os.getcwd(), dir), exist_ok=True)

from app import routes, models
