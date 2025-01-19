// Function to open the chatbot
function openChatbot() {
document.getElementById('chat-container').classList.remove('hidden');
document.getElementById('chat-icon').style.display = 'none'; // Hide the chat icon
}

// Function to close the chatbot
function closeChatbot() {
document.getElementById('chat-container').classList.add('hidden');
document.getElementById('chat-icon').style.display = 'block'; // Show the chat icon
}

