import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_TOKEN')
    REPO_URL = os.environ.get('REPO_URL')
    HUGGINGFACE_USERNAME = os.environ.get('HUGGINGFACE_USERNAME')  # New environment variable for the username

# Ensure required directories exist
required_dirs = ['uploads', 'models', 'backups', 'instance']
for dir in required_dirs:
    os.makedirs(os.path.join(os.getcwd(), dir), exist_ok=True)
