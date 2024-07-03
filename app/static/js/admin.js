document.addEventListener("DOMContentLoaded", function() {
    loadChatHistory();

    async function loadChatHistory() {
        const response = await fetch('/get_chat_history');
        const chatHistory = await response.json();
        const chatHistoryDiv = document.getElementById('chat-history');
        chatHistoryDiv.innerHTML = chatHistory.map(chat => `<p>${chat}</p>`).join('');
    }
});
