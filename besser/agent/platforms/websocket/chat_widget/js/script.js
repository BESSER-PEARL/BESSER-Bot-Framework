let ws;
let config;

function renderChatWidget(args) {
    config = args
    // Read values from the args dictionary
    const userName = config.userName || "Guest";
    const agentName = config.agentName || "Agent";
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
          <div id="chat-header" onclick="toggleChatWindow()" style="background-color:${themeColor}">${agentName}</div>
          <div id="chat-messages"></div>
          <!--
          <div id="typing-indicator">
              <img src="${typingAnimation}" alt="Agent is typing">
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
        displayMessage(payload, 'agent-message');
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
function getMessageHtml(message) {
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    messageElement.classList.add('html-message');
    return messageElement
}

// Function to generate a markdown message
function getMessageMarkdown(message) {
    const messageElement = document.createElement('div');
    messageElement.innerHTML = marked.parse(message);
    messageElement.classList.add('markdown-message');
    return messageElement
}

// Function to generate a string message
function getMessageStr(message) {
    const messageElement = document.createElement('p');
    messageElement.textContent = message;
    messageElement.classList.add('str-message');
    return messageElement;
}

// Function to generate an image message
function getMessageImage(message) {
    // Create an img element
    const imageElement = document.createElement('img');
    // Set the src attribute to the base64 string
    imageElement.src = `data:image/jpeg;base64,${message}`;
    imageElement.classList.add('image-message');
    return imageElement;
}

// Function to generate a dataframe (table) message
function getMessageDataframe(message) {
    // Parse the JSON string to an object
    const data = JSON.parse(message);

    // Create a table element
    const table = document.createElement('table');
    table.classList.add('dataframe-message');

    // Create the header row using the DataFrame column names
    const headerRow = document.createElement('tr');
    Object.keys(data).forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Determine the number of rows by checking the keys of the first column's data
    const numRows = Object.keys(data[Object.keys(data)[0]]).length;

    // Populate table rows with DataFrame values
    for (let i = 0; i < numRows; i++) {
        const row = document.createElement('tr');
        Object.keys(data).forEach(column => {
            const cell = document.createElement('td');
            cell.textContent = data[column][i.toString()]; // Access the value at the current index (as a string)
            row.appendChild(cell);
        });
        table.appendChild(row);
    }

    return table;
}

// Function to generate a file (download button) message
function getMessageFile(message) {
    const { name, type, base64 } = message; // Expected JSON structure in the message

    // Create a downloadable link element
    const downloadLink = document.createElement('a');
    downloadLink.href = `data:${type};base64,${base64}`;
    downloadLink.download = name;
    downloadLink.textContent = `Download ${name}`;
    downloadLink.classList.add('button');
    downloadLink.style.backgroundColor = config.themeColor;
    return downloadLink;
}

// Function to generate an options (buttons) message
function getMessageOptions(message) {
    // Create a container to hold the buttons
    const data = JSON.parse(message);
    const optionsContainer = document.createElement('div');
    optionsContainer.classList.add('options-message');

    // Iterate over each key-value pair in the options dictionary
    for (const [key, value] of Object.entries(data)) {
        // Create a button for each option
        const button = document.createElement('a');
        button.textContent = value;
        button.style.backgroundColor = config.themeColor;
        button.classList.add('button');

        // Set up click event to handle button selection
        button.addEventListener('click', () => {
            const messageInput = document.getElementById('message-input');
            messageInput.value = button.textContent;
            sendMessage()
        });

        optionsContainer.appendChild(button);
    }
    return optionsContainer;
}

// Function to generate a RAG message
function getMessageRAG(message) {
    const { answer, docs, llm_name, question } = message;

    // Create the main message element
    const messageElement = document.createElement('p');
    messageElement.textContent = `🔮 ${answer}`;
    messageElement.classList.add('str-message');

    // Create the "Details" clickable text
    const detailsLink = document.createElement('span');
    detailsLink.textContent = " [Details]";
    detailsLink.style.color = "blue";
    detailsLink.style.cursor = "pointer";

    // Create the expandable details section
    const detailsSection = document.createElement('div');
    detailsSection.style.display = 'none'; // Hidden by default

    const introText = document.createElement('p');
    introText.innerHTML = `This answer has been generated by an LLM: ${llm_name}<br>
                           It received the following documents as input to come up with a relevant answer:`;
    detailsSection.appendChild(introText);

    docs.forEach((doc, i) => {
        const docLabel = document.createElement('strong');
        docLabel.textContent = `Document ${i + 1}/${docs.length}`;
        detailsSection.appendChild(docLabel);

        const docList = document.createElement('ul');

        const sourceItem = document.createElement('li');
        sourceItem.textContent = `Source: ${doc.metadata.source}`;
        docList.appendChild(sourceItem);

        const pageItem = document.createElement('li');
        pageItem.textContent = `Page: ${doc.metadata.page}`;
        docList.appendChild(pageItem);

        const contentItem = document.createElement('li');
        contentItem.textContent = doc.content;
        contentItem.classList.add('str-message');
        docList.appendChild(contentItem);

        detailsSection.appendChild(docList);
    });

    // Toggle visibility when "Details" is clicked
    detailsLink.addEventListener('click', () => {
        if (detailsSection.style.display === 'none') {
            detailsSection.style.display = 'block';
            detailsLink.textContent = " [Hide Details]";
        } else {
            detailsSection.style.display = 'none';
            detailsLink.textContent = " [Details]";
        }
    });

    messageElement.appendChild(detailsLink);
    messageElement.appendChild(detailsSection);

    return messageElement;
}

// Function to generate a location (map) message
function getMessageLocation(message) {
    // Create a container for the map
    const mapContainer = document.createElement('div');
    mapContainer.classList.add('location-message');

    // Initialize the map after the container is added to the DOM
    setTimeout(() => {
        const map = L.map(mapContainer).setView([message.latitude, message.longitude], 13);

        // Set up the map tile layer (using OpenStreetMap tiles)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Add a marker at the specified location
        L.marker([message.latitude, message.longitude]).addTo(map)
            .bindPopup(`${message.latitude}, ${message.longitude}`);
    }, 0);

    return mapContainer;
}

// Function to generate a Plotly (chart) message
function getMessagePlotly(message) {
    // TODO: Colors are always black
    const chartWidth = 350;
    const chartHeight = 275;
    // Create the main chart container
    const chartContainer = document.createElement('div');
    chartContainer.classList.add('plotly-message');

    // Parse JSON data for the chart
    const chartJSON = JSON.parse(message);
    chartJSON.layout = chartJSON.layout || {};
    chartJSON.layout.autosize = true;
    chartJSON.layout.width = chartWidth;
    chartJSON.layout.height = chartHeight;
    chartJSON.layout.responsive = true;
    // Render the chart in the main container
    Plotly.newPlot(chartContainer, chartJSON.data, chartJSON.layout);

    // Create a button to trigger full-screen view
    const fullScreenButton = document.createElement('a');
    fullScreenButton.classList.add('button');
    fullScreenButton.textContent = 'View Full Screen';
    fullScreenButton.style.backgroundColor = config.themeColor;
    chartContainer.appendChild(fullScreenButton);

    // Full-screen modal setup
    const fullscreenModal = document.createElement('div');
    fullscreenModal.classList.add('plotly-fullscreen-modal');
    document.body.appendChild(fullscreenModal);

    // Full-screen chart container
    const fullscreenChartContainer = document.createElement('div');
    fullscreenChartContainer.classList.add('plotly-fullscreen-chart');
    fullscreenModal.appendChild(fullscreenChartContainer);

    // Open full-screen view when clicking the button
    fullScreenButton.addEventListener('click', () => {
        // Update layout size for full screen
        chartJSON.layout.width = window.innerWidth * 0.9; // 90% of window width
        chartJSON.layout.height = window.innerHeight * 0.9; // 90% of window height

        // Render the chart in full-screen container
        Plotly.newPlot(fullscreenChartContainer, chartJSON.data, chartJSON.layout);
        fullscreenModal.style.display = 'flex';
    });

    // Close full-screen view when clicking outside the chart
    fullscreenModal.addEventListener('click', (e) => {
        if (e.target === fullscreenModal) {
            chartJSON.layout.width = chartWidth;
            chartJSON.layout.height = chartHeight;
            Plotly.purge(fullscreenChartContainer); // Clear the full-screen chart
            fullscreenModal.style.display = 'none';
        }
    });

    return chartContainer;
}

function displayMessage(payload, className) {
    let messageElement;
    const chatMessages = document.getElementById('chat-messages');
    // hideTypingIndicator();
    if (['agent_reply_str', 'user_message'].includes(payload.action) && payload.message) {
        messageElement = getMessageStr(payload.message);
    }
    else if (payload.action === 'agent_reply_options' && payload.message) {
        messageElement = getMessageOptions(payload.message);
    }
    else if (payload.action === 'agent_reply_markdown' && payload.message) {
        messageElement = getMessageMarkdown(payload.message);
    }
    else if (payload.action === 'agent_reply_html' && payload.message) {
        messageElement = getMessageHtml(payload.message);
    }
    else if (payload.action === 'agent_reply_image' && payload.message) {
        messageElement = getMessageImage(payload.message);
    }
    else if (payload.action === 'agent_reply_file' && payload.message) {
        messageElement = getMessageFile(payload.message);
    }
    else if (payload.action === 'agent_reply_dataframe' && payload.message) {
        messageElement = getMessageDataframe(payload.message);
    }
    else if (payload.action === 'agent_reply_rag' && payload.message) {
        messageElement = getMessageRAG(payload.message);
    }
    else if (payload.action === 'agent_reply_location' && payload.message) {
        messageElement = getMessageLocation(payload.message);
    }
    else if (payload.action === 'agent_reply_plotly' && payload.message) {
        messageElement = getMessagePlotly(payload.message);
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

