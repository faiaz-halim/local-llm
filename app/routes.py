import os
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from app.models import ChatHistory, UploadedFile
from transformers import AutoModelForCausalLM, AutoTokenizer
import git

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
MODELS_FOLDER = os.path.join(os.getcwd(), 'models')
BACKUPS_FOLDER = os.path.join(os.getcwd(), 'backups')
MODEL_PATH = os.path.join(MODELS_FOLDER, 'mistral-7b-instruct-v0.3')
HUGGINGFACE_TOKEN = app.config['HUGGINGFACE_TOKEN']
REPO_URL = app.config['REPO_URL']
HUGGINGFACE_USERNAME = app.config['HUGGINGFACE_USERNAME']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure required directories exist
required_dirs = ['uploads', 'models', 'backups', 'instance']
for dir in required_dirs:
    os.makedirs(os.path.join(os.getcwd(), dir), exist_ok=True)

def clone_repo(repo_url, clone_dir, username, token):
    if not os.path.exists(clone_dir):
        os.makedirs(clone_dir, exist_ok=True)
        repo_url_with_auth = repo_url.replace("https://", f"https://{username}:{token}@")
        git.Repo.clone_from(repo_url_with_auth, clone_dir, branch='main')

def load_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    return tokenizer, model

# Clone the repository if it doesn't exist
clone_repo(REPO_URL, MODEL_PATH, HUGGINGFACE_USERNAME, HUGGINGFACE_TOKEN)
tokenizer, model = load_model(MODEL_PATH)

@app.route('/')
def chat():
    return render_template('chat.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/chat', methods=['POST'])
def chat_with_model():
    data = request.json
    message = data['message']
    model_name = data['model']
    response = get_model_response(model_name, message)
    save_chat_history(message, response)
    return jsonify({'response': response})

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    chat_history = ChatHistory.query.all()
    chat_history_list = [{'user': chat.user_message, 'response': chat.response_message} for chat in chat_history]
    return jsonify(chat_history_list)

@app.route('/upload_files', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        save_uploaded_file(filename)
        return redirect(url_for('admin'))

@app.route('/retrain_model', methods=['POST'])
def retrain_model():
    backup_current_model()
    retrain_model_with_files()
    return redirect(url_for('admin'))

@app.route('/get_models', methods=['GET'])
def get_models():
    models = os.listdir(MODELS_FOLDER)
    return jsonify(models)

def get_model_response(model_name, message):
    model_path = os.path.join(MODELS_FOLDER, model_name)
    tokenizer, model = load_model(model_path)
    inputs = tokenizer.encode(message, return_tensors="pt")
    outputs = model.generate(inputs, max_length=100)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

def save_chat_history(user_message, response_message):
    chat = ChatHistory(user_message=user_message, response_message=response_message)
    db.session.add(chat)
    db.session.commit()

def save_uploaded_file(filename):
    uploaded_file = UploadedFile(filename=filename)
    db.session.add(uploaded_file)
    db.session.commit()

def backup_current_model():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_filename = f'model_backup_{timestamp}.pth'
    # Placeholder for backing up the model
    with open(os.path.join(BACKUPS_FOLDER, backup_filename), 'w') as f:
        f.write('Backup model data.')

def retrain_model_with_files():
    # Placeholder function to retrain the model with files in UPLOAD_FOLDER
    new_model_filename = 'retrained_model.pth'
    with open(os.path.join(MODELS_FOLDER, new_model_filename), 'w') as f:
        f.write('Retrained model data.')
