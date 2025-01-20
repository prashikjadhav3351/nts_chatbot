const chatInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// Show/hide send button based on input
chatInput.addEventListener('input', () => {
    if (chatInput.value.trim() !== '') {
        sendBtn.style.display = 'flex';
        sendBtn.disabled = false;
    } else {
        sendBtn.style.display = 'none';
        sendBtn.disabled = true;
    }
});
