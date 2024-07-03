# Run
1. Ensure Ollama is installed and running on your system. `curl -fsSL https://ollama.com/install.sh | sh` or download from https://ollama.com/download
2. Make sure you have the Mistral model pulled in Ollama: `ollama pull mistral`
3. Create a python virtual env and activate it: `python3 -m venv env && source env/bin/activate`
3. Install the required packages: `pip install -r requirements.txt`
4. Run the application: `python run.py`

# Usage
1. Register and login with an user (working)
2. Chat with base mistral model (working)
3. See chat history in Admin Chats page (working)
4. Upload documents through the admin interface (working)
5. Train the model using the uploaded documents (not working)
6. Chat with the custom-trained model (not working)