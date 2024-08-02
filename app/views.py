from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User, ChatHistory
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
import os
import requests
import json
import docx
import pandas as pd
from PyPDF2 import PdfReader

def get_ollama_response(prompt):
    model_name = 'mistral'
    url = f"http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    payload = {"model": model_name, "prompt": prompt}
    response = requests.post(url, json=payload, headers=headers, stream=True)

    full_response = ""

    try:
        for line in response.iter_lines():
            if line:
                json_response = json.loads(line.decode('utf-8'))
                full_response += json_response.get('response', '')
                if json_response.get('done', False):
                    break
    except json.JSONDecodeError as e:
        print("Error decoding the response:", e)
        return "Error decoding the response."

    return full_response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        if prompt:
            response = get_ollama_response(prompt)
            chat = ChatHistory(prompt=prompt, response=response)
            db.session.add(chat)
            db.session.commit()
            return jsonify({'prompt': prompt, 'response': response})
    return render_template('chat.html', title='Chat')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat_history'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('chat_history')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat_history'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/chat_history')
@login_required
def chat_history():
    chats = ChatHistory.query.order_by(ChatHistory.timestamp.desc()).all()
    return render_template('chat_history.html', title='Chat History', chats=chats)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            return redirect(url_for('upload'))
    return render_template('upload.html')

def read_txt(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def read_docx(file_path):
    doc = docx.Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs])

def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return '\n'.join(text)

def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_string()

def create_modelfile():
    uploads_dir = app.config['UPLOAD_FOLDER']
    model_content = []

    for filename in os.listdir(uploads_dir):
        file_path = os.path.join(uploads_dir, filename)
        if filename.endswith('.txt'):
            content = read_txt(file_path)
        elif filename.endswith('.docx'):
            content = read_docx(file_path)
        elif filename.endswith('.pdf'):
            content = read_pdf(file_path)
        elif filename.endswith('.csv'):
            content = read_csv(file_path)
        else:
            continue

        model_content.append(f"DATA FILE {filename}\n{content}\n")

    modelfile_content = (
        "FROM mistral\n"
        "PARAMETER temperature 0.7\n"
        "PARAMETER num_ctx 4096\n"
        "PARAMETER top_p 0.9\n"
        "SYSTEM You are an AI assistant specialized in cybersecurity.\n"
    ) + "\n".join(model_content)

    return modelfile_content

def train_model(modelfile_content):
    model_name = "mario"
    api_url = "http://localhost:11434/api/create"
    payload = {
        "name": model_name,
        "modelfile": modelfile_content
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        flash('Model trained and saved successfully.')
    else:
        flash(f"Error training model: {response.text}")

@app.route('/create_modelfile', methods=['POST'])
@login_required
def create_modelfile_route():
    modelfile_content = create_modelfile()
    flash('Modelfile created successfully.')
    return redirect(url_for('upload'))

@app.route('/train_model', methods=['POST'])
@login_required
def train_model_route():
    modelfile_content = create_modelfile()
    train_model(modelfile_content)
    return redirect(url_for('upload'))