
let isVoiceMessage = false;
let recognition;

function sendMessage(fromVoice = false) {
    isVoiceMessage = fromVoice;
    const userInput = document.getElementById('user-input').value.trim();
    if (!userInput) return;

    appendMessage(userInput, 'user');
    document.getElementById('user-input').value = '';

    appendMessage('<div class="typing-indicator"><span></span><span></span><span></span></div>', 'bot');

    setTimeout(() => {
        document.querySelector('#chat-box .typing-indicator').remove();
        fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userInput }),
        })
        .then(response => response.json())
        .then(data => {
            appendMessage(data.answer, 'bot');
            if (isVoiceMessage) speakText(data.answer);
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage('Something went wrong. Please try again.', 'bot');
        });
    }, 2000);
}

function appendMessage(message, sender) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.innerHTML = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage(false);
}

function startVoiceRecognition() {
    const micButton = document.getElementById('mic-btn');

    if (!('webkitSpeechRecognition' in window)) {
        appendMessage('Speech recognition is not supported in this browser.', 'bot');
        return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => micButton.classList.add('mic-active');
    recognition.onend = () => micButton.classList.remove('mic-active');
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('user-input').value = transcript;
        sendMessage(true);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        appendMessage('Sorry, I could not understand. Please try again.', 'bot');
        micButton.classList.remove('mic-active');
    };

    recognition.start();
}

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
}

window.addEventListener('beforeunload', () => {
    if (recognition) recognition.abort();
    window.speechSynthesis.cancel();
});
