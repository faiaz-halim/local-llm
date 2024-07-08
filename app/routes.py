import os
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from app.models import ChatHistory, UploadedFile
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download
from tqdm.auto import tqdm

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
MODELS_FOLDER = os.path.join(os.getcwd(), 'models')
BACKUPS_FOLDER = os.path.join(os.getcwd(), 'backups')
MODEL_PATH = os.path.join(MODELS_FOLDER, 'mistral-7b-instruct-v0.3')
HUGGINGFACE_TOKEN = app.config['HUGGINGFACE_TOKEN']
REPO_ID = app.config['REPO_URL']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure required directories exist
required_dirs = ['uploads', 'models', 'backups', 'instance']
for dir in required_dirs:
    os.makedirs(os.path.join(os.getcwd(), dir), exist_ok=True)

class TqdmProgress(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update_to(self, blocks=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(blocks * bsize - self.n)

def download_model(repo_id, model_path, token):
    if not os.path.exists(model_path):
        os.makedirs(model_path, exist_ok=True)
        print(f"Downloading {repo_id} model...")
        snapshot_download(
            repo_id,
            use_auth_token=token,
            local_dir=model_path,
            local_dir_use_symlinks=False,
        )

def load_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    return tokenizer, model

# Download model if it doesn't exist
download_model(REPO_ID, MODEL_PATH, HUGGINGFACE_TOKEN)
try:
    tokenizer, model = load_model(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    raise

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
    chat = ChatHistory(user_message=user_message, response_message=json.dumps(response_message))
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
