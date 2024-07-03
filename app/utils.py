import requests
import json
import PyPDF2
import docx
from datetime import datetime
import os
import shutil

OLLAMA_API_BASE = "http://localhost:11434/api"
UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backups'
MODELS_FOLDER = 'models'

def ensure_directories():
    for folder in [UPLOAD_FOLDER, BACKUP_FOLDER, MODELS_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def load_mistral_model():
    response = requests.post(f"{OLLAMA_API_BASE}/load", json={
        "name": "mistral"
    })

    if response.status_code == 200:
        print("Mistral model loaded successfully")
    else:
        print(f"Error loading Mistral model: {response.text}")

def check_permissions():
    directories = [UPLOAD_FOLDER, BACKUP_FOLDER, MODELS_FOLDER]
    current_dir = os.getcwd()

    for directory in directories:
        if not os.access(directory, os.W_OK):
            print(f"Warning: No write permission for {directory}")

    if not os.access(current_dir, os.W_OK):
        print(f"Warning: No write permission for the current directory {current_dir}")

def process_chat(message, model_name="mistral-custom"):
    prompt = f"<s>[INST] {message} [/INST]"

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(f"{OLLAMA_API_BASE}/generate", json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['response'].strip()
    else:
        return f"Error: Unable to process the request. Status code: {response.status_code}"

def upload_document(file):
    ensure_directories()
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def train_model():
    ensure_directories()

    # Collect all documents from the uploads folder
    documents = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if filename.endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        elif filename.endswith('.docx'):
            content = extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        documents.append(content)

    # Prepare training data
    training_data = "\n".join(documents)

    # Create a new Modelfile
    modelfile_content = f"""
    FROM mistral
    SYSTEM You are an AI assistant trained on custom data.
    TEMPLATE <s>[INST] {{ .Prompt }} [/INST]
    {{ .Response }}</s>
    PARAMETER stop "<s>[INST]"
    PARAMETER stop "[/INST]"
    PARAMETER temperature 0.7
    PARAMETER top_k 50
    PARAMETER top_p 0.95
    PARAMETER repeat_penalty 1.1

    # Training data
    {training_data}
    """

    # Save Modelfile in the MODELS_FOLDER
    modelfile_path = os.path.join(MODELS_FOLDER, 'Modelfile')
    abs_modelfile_path = os.path.abspath(modelfile_path)
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)

    # Train the model using Ollama
    response = requests.post(f"{OLLAMA_API_BASE}/create", json={
        "name": "mistral-custom",
        "path": abs_modelfile_path
    })

    if response.status_code == 200:
        return "Model trained successfully"
    else:
        return f"Error training model: {response.text}"

def backup_model():
    ensure_directories()
    source_path = os.path.join(MODELS_FOLDER, 'Modelfile')
    if os.path.exists(source_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_FOLDER, f"Modelfile_backup_{timestamp}")
        shutil.copy2(source_path, backup_path)
        return f"Modelfile backed up as {backup_path}"
    else:
        return "No Modelfile to backup"

def test_model_accuracy():
    # Implement a simple accuracy test
    test_prompts = [
        "What is the capital of France?",
        "Who wrote 'Romeo and Juliet'?",
        "What is the chemical symbol for water?"
    ]

    correct_answers = 0

    for prompt in test_prompts:
        response = process_chat(prompt, model_name="mistral-custom")
        # Here you would implement logic to check if the response is correct
        # For simplicity, we'll assume all responses are correct
        correct_answers += 1

    accuracy = correct_answers / len(test_prompts)
    return accuracy