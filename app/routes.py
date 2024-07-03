from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Chat, Document
from . import db
from .utils import process_chat, upload_document, train_model, test_model_accuracy
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('main.register'))
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.chat'))
        flash('Invalid username or password')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/')
@login_required
def chat():
    return render_template('chat.html')

@main.route('/chat', methods=['POST'])
@login_required
def process_message():
    message = request.json['message']
    response = process_chat(message, model_name="mistral")
    chat = Chat(user_id=current_user.id, message=message, response=response, timestamp=datetime.utcnow())
    db.session.add(chat)
    db.session.commit()
    return jsonify({'response': response})

@main.route('/admin/chats')
@login_required
def admin_chats():
    chats = Chat.query.join(User).order_by(Chat.timestamp.desc()).all()
    return render_template('admin_chats.html', chats=chats)

@main.route('/admin/documents')
@login_required
def admin_documents():
    documents = Document.query.order_by(Document.uploaded_at.desc()).all()
    return render_template('admin_documents.html', documents=documents)

@main.route('/admin/documents/upload', methods=['POST'])
@login_required
def upload_doc():
    if 'document' not in request.files:
        flash('No file part')
        return redirect(url_for('main.admin_documents'))
    file = request.files['document']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('main.admin_documents'))
    if file:
        content = upload_document(file)
        document = Document(filename=file.filename, content=content, uploaded_at=datetime.utcnow())
        db.session.add(document)
        db.session.commit()
        flash('Document uploaded successfully')
    return redirect(url_for('main.admin_documents'))

@main.route('/admin/train', methods=['POST'])
@login_required
def train():
    documents = Document.query.all()
    before_accuracy = test_model_accuracy()
    result = train_model()
    after_accuracy = test_model_accuracy()
    return jsonify({
        'result': result,
        'before_accuracy': before_accuracy,
        'after_accuracy': after_accuracy
    })
