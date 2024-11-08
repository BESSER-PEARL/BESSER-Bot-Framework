let ws;
let config;

function renderChatWidget(args) {
    config = args
    // Read values from the args dictionary
    const userName = config.userName || "Guest";
    const chatbotName = config.chatbotName || "Chatbot";
    const themeColor = config.themeColor || "#2ecc71";
    const wsAddress = config.wsAddress || "ws://localhost:8765";
    const messageInputPlaceHolder = config.messageInputPlaceHolder || "Type a message...";
    const icon = config.icon || "https://www.drupal.org/files/project-images/xatkit.png";
    const typingAnimation = config.typingAnimation || "https://c.tenor.com/EZc7Xubv14AAAAAC/tenor.gif";

    // Define the HTML structure
    const container = document.getElementById('chat-widget');
    const chatWidgetHTML = `
        <!-- Chat widget container -->
        <div id="chat-window">
          <div id="chat-header" onclick="toggleChatWindow()" style="background-color:${themeColor}">${chatbotName}</div>
          <div id="chat-messages"></div>
          <!--
          <div id="typing-indicator">
              <img src="${typingAnimation}" alt="Bot is typing">
          </div>
          -->
          <div id="chat-input">
            <input type="text" id="message-input" placeholder="${messageInputPlaceHolder}">
            <button onclick="sendMessage()" style="background-color:${themeColor}">Send</button>
          </div>
        </div>
        
        <!-- Circle button with custom image to show the chat window -->
        <div id="circle-button" onclick="toggleChatWindow()">
          <img src="${icon}" alt="Chat Icon">
        </div>
    `;
    // Insert the HTML structure into the container
    container.innerHTML = chatWidgetHTML;

    ws = new WebSocket(wsAddress);

    const messageInput = document.getElementById('message-input');
    const circleButton = document.getElementById('circle-button');

    ws.onopen = () => console.log('Connected to WebSocket server');
    ws.onclose = () => console.log('Disconnected from WebSocket server');
    ws.onerror = (error) => console.error('WebSocket error:', error);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        displayMessage(payload, 'bot-message');
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    // Add a click event to toggle the spin class
    circleButton.addEventListener('click', () => {
      circleButton.classList.toggle('spin');
    });

    messageInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
      }
    });
}

function sendMessage() {
  const messageInput = document.getElementById('message-input');
  const message = messageInput.value;
  if (message) {
    const payload = {
      action: 'user_message',
      message: message,
    };
    displayMessage(payload, 'user-message');
    ws.send(JSON.stringify(payload));
    messageInput.value = '';
    //showTypingIndicator();
  }
}

  // Function to generate a html message
  function getMessageHtml(text) {
    const messageElement = document.createElement('div');
    messageElement.innerHTML = text;
    messageElement.classList.add('html-message');
    return messageElement
  }

  // Function to generate a markdown message
  function getMessageMarkdown(text) {
    const messageElement = document.createElement('div');
    messageElement.innerHTML = marked.parse(text);
    messageElement.classList.add('markdown-message');
    return messageElement
  }

 // Function to generate a string message
  function getMessageStr(text) {
    const messageElement = document.createElement('p');
    messageElement.textContent = text;
    messageElement.classList.add('str-message');
    return messageElement;
  }

  function displayMessage(payload, className) {
    let messageElement;
    const chatMessages = document.getElementById('chat-messages');
    // hideTypingIndicator();
    if (['bot_reply_str', 'user_message'].includes(payload.action) && payload.message) {
      messageElement = getMessageStr(payload.message);
    }
    else if (payload.action === 'bot_reply_markdown' && payload.message) {
      messageElement = getMessageMarkdown(payload.message);
    }
    else if (payload.action === 'bot_reply_html' && payload.message) {
      messageElement = getMessageHtml(payload.message);
    }
    else {
      console.warn('Received unknown message format:', payload);
    }
    messageElement.classList.add(className);
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to latest message
  }

function toggleChatWindow() {
    const chatWindow = document.getElementById('chat-window');
    if (chatWindow.classList.contains('visible')) {
    chatWindow.classList.remove('visible');
    setTimeout(() => {
      chatWindow.style.visibility = 'hidden';
    }, 300); // Delay for the fade-out transition
  } else {
    chatWindow.style.visibility = 'visible';
    chatWindow.classList.add('visible');
  }
}

// Show typing indicator
function showTypingIndicator() {
  const typingIndicator = document.getElementById('typing-indicator');
  typingIndicator.style.display = 'block';
}

// Hide typing indicator
function hideTypingIndicator() {
  const typingIndicator = document.getElementById('typing-indicator');
  typingIndicator.style.display = 'none';
}

