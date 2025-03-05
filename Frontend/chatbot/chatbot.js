// Tour
let tour;
const initializeTour = () => {
    tour = new Shepherd.Tour({
      defaultStepOptions: {
        classes: 'shepherd-theme-custom',
        scrollTo: { behavior: 'smooth', block: 'center' }
      }
    });

    // Step 1: Upload Button
    tour.addStep({
        id: 'upload-step',
        text: 'Click here to upload documents (images/PDFs) for auto-filling the form!',
        attachTo: {
        element: '.chatbot-upload-btn',
        on: 'right'
        },
        buttons: [
        { text: 'Next', action: tour.next }
        ]
    });

    // Step 2: Input Field
    tour.addStep({
        id: 'input-step',
        text: 'Type your questions here about account opening or banking services',
        attachTo: {
        element: '.chatbot-input',
        on: 'top'
        },
        buttons: [
        { text: 'Back', action: tour.back },
        { text: 'Next', action: tour.next }
        ]
    });

    // Step 3: Minimize Button
    tour.addStep({
        id: 'minimize-step',
        text: 'Click here to minimize the chat window when you need more space',
        attachTo: {
        element: '.minimize-btn',
        on: 'left'
        },
        buttons: [
        { text: 'Back', action: tour.back },
        { text: 'Finish', action: tour.complete }
        ]
    });
};

// ======================
// Chatbot State Management
// ======================
let chatHistory = JSON.parse(sessionStorage.getItem('chatHistory')) || [];
let isChatVisible = (sessionStorage.getItem('chatVisible') || 'true') === 'true';;

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

const addMessage = (text, type, options = {}) => {
    const messageContainer = document.getElementById('chatbot-messages');
    const div = document.createElement('div');
    div.classList.add('message', type);
    div.textContent = text;
    if (options.id) {
        div.setAttribute('data-id', options.id);
    }
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
let currentThreadId = localStorage.getItem('chatThreadId') || '';
const sendMessage = async () => {
    const inputField = document.getElementById('chatbot-input');
    const message = inputField.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    inputField.value = '';

    if (!currentThreadId) {
        currentThreadId = crypto.randomUUID();
        localStorage.setItem('chatThreadId', currentThreadId);
    }
    
    try {
        const response = await fetch('/chatbot', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-Thread-ID': currentThreadId 
        },
        body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        console.log(data)
        addMessage(data.response, 'bot');
        currentThreadId = data.thread_id; // Update if new thread created
        localStorage.setItem('chatThreadId', currentThreadId);
    } catch (error) {
        addMessage('Sorry, there was an error processing your request.', 'bot');
        console.error('Chat error:', error);
    }
};

// progress bar

// Show the progress bar container and reset its value
const showProgressBar = () => {
    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('upload-progress');
    if (progressContainer && progressBar) {
      progressBar.value = 0;
      progressContainer.style.display = 'block';
    }
  };
  
  // Update the progress bar value
  const updateProgressBar = (percent) => {
    const progressBar = document.getElementById('upload-progress');
    if (progressBar) {
      progressBar.value = percent;
    }
  };
  
  // Hide the progress bar container
  const hideProgressBar = () => {
    const progressContainer = document.getElementById('upload-progress-container');
    if (progressContainer) {
      progressContainer.style.display = 'none';
    }
  };
  
  // Add a processing message to the chat
  const showProcessingMessage = () => {
    // Optionally, add a special flag so you can remove this specific message later.
    addMessage('Files are being processed...', 'bot', { id: 'processing-msg' });
  };
  
  // Remove the processing message from the chat
  const removeProcessingMessage = () => {
    const messageContainer = document.getElementById('chatbot-messages');
    const processingMsg = messageContainer.querySelector('[data-id="processing-msg"]');
    if (processingMsg) {
      processingMsg.remove();
    }
  };
  

// ======================
// File Upload Handling
// ======================
const handleFileUpload = async (event) => {
    const uploadedFiles  = Array.from(event.target.files).slice(0, 5);
    if (!uploadedFiles ) return;

    try {

        // Show progress bar and processing message
        showProgressBar();
        showProcessingMessage();

        const formData = new FormData();
        uploadedFiles.forEach(file => formData.append('files', file));

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload');

        // Listen for progress events on the upload
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            console.log(`Progress: ${percentComplete}% (loaded: ${e.loaded} bytes, total: ${e.total} bytes)`);
            updateProgressBar(percentComplete);
            }
        });

        xhr.onload = function () {
            // Hide progress bar after completion
            hideProgressBar();
            // Remove the processing message
            removeProcessingMessage();
        
            if (xhr.status >= 200 && xhr.status < 300) {
              const response = JSON.parse(xhr.responseText);
              const { data, conflicts } = response;
              if (conflicts) {
                const conflictMessage = `Conflicts detected:\n${Object.entries(conflicts)
                  .map(([field, values]) => `${field}: ${values.join(' vs ')}`)
                  .join('\n')}`;
                addMessage(conflictMessage, 'bot');
              } else {
                processUploadedData(data, `${uploadedFiles.length} files processed`);
              }
            } else {
              addMessage('Failed to process the uploaded file.', 'bot');
              console.error('Upload error:', xhr.statusText);
            }
        };

        xhr.onerror = function () {
            hideProgressBar();
            removeProcessingMessage();
            addMessage('Failed to process the uploaded file.', 'bot');
            console.error('Upload error:', xhr.statusText);
        };
        
        xhr.send(formData);
        event.target.value = ''; // Reset file input

        // const response = await fetch('/upload', {
        //     method: 'POST',
        //     body: formData
        // });
        
        // const { data, conflicts } = await response.json();
        // if (conflicts) {
        //     const conflictMessage = `Conflicts detected:\n${Object.entries(conflicts)
        //         .map(([field, values]) => `${field}: ${values.join(' vs ')}`)
        //         .join('\n')}`;
        //     addMessage(conflictMessage, 'bot');
        // } else {
        //     processUploadedData(data, `${uploadedFiles.length} files processed`);
        // }
        // event.target.value = ''; // Reset file input
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

    console.log("In toggle");
    console.log(localStorage.getItem('tourCompleted'));
    // comment out this reset the tour when chat is minimized
    if (!isChatVisible) {
        localStorage.removeItem('tourCompleted');
    }
};

// ======================
// Initialization
// ======================
let isInitialized = false;
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
        addMessage(
            "Hello! I'm am Wells Fargo's new AI assistant. " + 
            "I'm here to answer any quiries you have about Wells Fargo products" +
            " and you can use my new Autofill feature to automate the form filling process by uploading your documents(images and pdfs)." + 
            " To know more, start a conversation by saying Hi or say Hello or ask your questions right away.", 
            'bot'
        );
    } else {
        // Scroll to bottom if history exists
        const messageContainer = document.getElementById('chatbot-messages');
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    document.querySelector('.chatbot-button').addEventListener('click', toggleChatbot);
    
    // Set initial visibility
    // document.getElementById('chatbot').classList.remove('visible'); // Force hidden initially
    document.querySelector('.chatbot-button').style.display = isChatVisible ? 'none' : 'block';


    // Event Listeners
    document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    document.querySelector('.chatbot-send-btn').addEventListener('click', sendMessage);
    document.getElementById('chatbot-upload').addEventListener('change', handleFileUpload);
    document.querySelector('.minimize-btn').addEventListener('click', toggleChatbot);

    console.log(localStorage.getItem('tourCompleted'));
    // if (!localStorage.getItem('tourCompleted')) {
        setTimeout(() => {
          initializeTour();
          tour.start();
          localStorage.setItem('tourCompleted', 'true');
        }, 2000); // Start tour 2 seconds after page load
    // }
    console.log(localStorage.getItem('tourCompleted'));
};

// Export functions for module usage
export { initializeChatbot, toggleChatbot, sendMessage, handleFileUpload };