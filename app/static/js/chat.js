document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatInterface = document.getElementById('chat-interface');
    const modelSelect = document.getElementById('model-select');

    loadModels();

    chatForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const userMessage = userInput.value;
        userInput.value = '';
        chatInterface.innerHTML += `<p><strong>You:</strong> ${userMessage}</p>`;

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage, model: modelSelect.value })
        });

        const data = await response.json();
        chatInterface.innerHTML += `<p><strong>LLM:</strong> ${data.response}</p>`;
        chatInterface.scrollTop = chatInterface.scrollHeight;
    });

    async function loadModels() {
        const response = await fetch('/get_models');
        const models = await response.json();
        modelSelect.innerHTML = models.map(model => `<option value="${model}">${model}</option>`).join('');
    }
});
