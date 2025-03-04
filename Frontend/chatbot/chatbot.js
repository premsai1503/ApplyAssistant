// Frontend/chatbot/chatbot.js

// ======================
// Chatbot State Management
// ======================
let chatHistory = JSON.parse(sessionStorage.getItem('chatHistory')) || [];
let isChatVisible = sessionStorage.getItem('chatVisible') === 'true';

const saveChatState = () => {
    sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    sessionStorage.setItem('chatVisible', isChatVisible.toString());
};

// ======================
// Core Chatbot Functions
// ======================
const loadChatHistory = () => {
    const messageContainer = document.getElementById('chatbot-messages');
    messageContainer.innerHTML = '';
    
    chatHistory.forEach(msg => {
        const div = document.createElement('div');
        div.classList.add('message', msg.type);
        div.textContent = msg.text;
        messageContainer.appendChild(div);
    });
    
    messageContainer.scrollTop = messageContainer.scrollHeight;
    setTimeout(() => {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }, 50);
};

const addMessage = (text, type) => {
    const messageContainer = document.getElementById('chatbot-messages');
    const div = document.createElement('div');
    div.classList.add('message', type);
    div.textContent = text;
    messageContainer.appendChild(div);
    
    chatHistory.push({ text, type });
    saveChatState();
    messageContainer.scrollTop = messageContainer.scrollHeight;
    window.addEventListener('resize', () => {
        const messageContainer = document.getElementById('chatbot-messages');
        messageContainer.scrollTop = messageContainer.scrollHeight;
    });
};

// ======================
// Message Handling
// ======================
const sendMessage = async () => {
    const inputField = document.getElementById('chatbot-input');
    const message = inputField.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    inputField.value = '';
    
    try {
        const response = await fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        addMessage(data.response, 'bot');
    } catch (error) {
        addMessage('Sorry, there was an error processing your request.', 'bot');
        console.error('Chat error:', error);
    }
};

// ======================
// File Upload Handling
// ======================
const handleFileUpload = async (event) => {
    const uploadedFiles  = Array.from(event.target.files).slice(0, 5);
    if (!uploadedFiles ) return;

    try {
        const formData = new FormData();
        uploadedFiles.forEach(file => formData.append('files', file));

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const { data, conflicts } = await response.json();
        if (conflicts) {
            const conflictMessage = `Conflicts detected:\n${Object.entries(conflicts)
                .map(([field, values]) => `${field}: ${values.join(' vs ')}`)
                .join('\n')}`;
            addMessage(conflictMessage, 'bot');
        } else {
            processUploadedData(data, `${uploadedFiles.length} files processed`);
        }
        event.target.value = ''; // Reset file input
    } catch (error) {
        addMessage('Failed to process the uploaded file.', 'bot');
        console.error('Upload error:', error);
    }
};

const processUploadedData = (data, filename) => {
    const fieldMapping = {
        SSN: 'SSN',
        MobileNumber: 'MobileNumber',
        FirstName: 'FirstName',
        LastName: 'LastName',
        Sex: 'Sex',
        PassportNumber: 'PassportNumber',
        PermanentAccountNumber: 'PermanentAccountNumber',
        Nationality: 'Nationality',
        DateofBirth: 'DateofBirth',
        PlaceofBirth: 'PlaceofBirth',
        DateofIssue: 'DateofIssue',
        DateofExpiration: 'DateofExpiration'
    };

    let missingFields = [];
    
    Object.entries(fieldMapping).forEach(([key, fieldId]) => {
        const inputField = document.getElementById(fieldId);
        if (!inputField) return;
        
        const value = data[key]?.trim();
        if (value && !["NOT FOUND", "Not Found", "not found"].includes(value)) {
            inputField.value = value;
        } else {
            missingFields.push(key);
        }
    });

    const message = missingFields.length > 0
        ? `Received ${filename}. Missing fields: ${missingFields.join(', ')}`
        : `Received ${filename}. All fields extracted successfully.`;

    addMessage(message, 'bot');
};

// ======================
// UI Controls
// ======================
const toggleChatbot = () => {
    const chatbot = document.getElementById('chatbot');
    const chatButton = document.querySelector('.chatbot-button');
    
    isChatVisible = !isChatVisible;
    chatbot.classList.toggle('visible', isChatVisible);
    chatButton.style.display = isChatVisible ? 'none' : 'block';
    saveChatState();
};

// ======================
// Initialization
// ======================
let isInitialized = false; // Add this flag
const initializeChatbot = () => {
    
    if (isInitialized) return;
    isInitialized = true;

    // Remove existing listeners first
    const chatButton = document.querySelector('.chatbot-button');
    chatButton.removeEventListener('click', toggleChatbot);
    
    // Add fresh listener
    chatButton.addEventListener('click', toggleChatbot);
    
    // Load existing chat history
    loadChatHistory();
    
    // Modified initial message check
    if (chatHistory.length === 0) {
        addMessage('Hello! I can help automate your form filling process...', 'bot');
    } else {
        // Scroll to bottom if history exists
        const messageContainer = document.getElementById('chatbot-messages');
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    document.querySelector('.chatbot-button').addEventListener('click', toggleChatbot);
    
    // Set initial visibility
    document.getElementById('chatbot').classList.remove('visible'); // Force hidden initially
    document.querySelector('.chatbot-button').style.display = 'block';
    
    // Add initial message if empty
    if (chatHistory.length === 0) {
        addMessage('Hello! I can help automate your form filling process. You can upload documents and I\'ll fill the form for you.', 'bot');
    }

    // Event Listeners
    document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    document.querySelector('.chatbot-send-btn').addEventListener('click', sendMessage);
    document.getElementById('chatbot-upload').addEventListener('change', handleFileUpload);
    document.querySelector('.minimize-btn').addEventListener('click', toggleChatbot);
};

// Export functions for module usage
export { initializeChatbot, toggleChatbot, sendMessage, handleFileUpload };