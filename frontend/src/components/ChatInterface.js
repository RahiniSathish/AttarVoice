class ChatInterface {
    constructor(container) {
        this.container = container;
        this.messages = [];
        this.isLoading = false;
        this.apiUrl = 'http://localhost:8080';
        this.init();
    }

    init() {
        this.loadMessages();
        this.setupEventListeners();
    }

    render() {
        this.container.innerHTML = `
            <div class="chat-container">
                ${this.renderHeader()}
                ${this.renderMessages()}
                ${this.renderInputArea()}
            </div>
        `;
        this.setupEventListeners();
        this.scrollToBottom();
    }

    renderHeader() {
        return `
            <div class="chat-header">
                <div class="header-content">
                    <div>
                        <div class="header-title">
                            <span class="header-icon">🎙️</span>
                            <div>
                                <div>Travel.ai Travel Assistant</div>
                                <div class="header-subtitle">Powered by Vapi + Yellow.ai</div>
                            </div>
                        </div>
                    </div>
                    <div class="header-actions">
                        <button class="header-btn" id="clearBtn" title="Clear chat">🗑️</button>
                        <button class="header-btn" id="infoBtn" title="Info">ℹ️</button>
                    </div>
                </div>
            </div>
        `;
    }

    renderMessages() {
        if (this.messages.length === 0) {
            return `
                <div class="messages-container">
                    <div class="empty-state">
                        <div class="empty-icon">✈️</div>
                        <div class="empty-text">Start planning your trip!</div>
                        <div class="empty-text" style="font-size: 12px; opacity: 0.5;">
                            Ask me about flights, hotels, or bookings
                        </div>
                    </div>
                </div>
            `;
        }

        const messagesHtml = this.messages.map((msg, index) => `
            <div class="message ${msg.type}">
                <div class="message-avatar">${msg.type === 'user' ? '👤' : '🤖'}</div>
                <div>
                    <div class="message-bubble">${this.escapeHtml(msg.content)}</div>
                    <div class="message-time">${msg.time}</div>
                </div>
            </div>
        `).join('');

        const typingHtml = this.isLoading ? `
            <div class="message ai">
                <div class="message-avatar">🤖</div>
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        ` : '';

        return `<div class="messages-container">${messagesHtml}${typingHtml}</div>`;
    }

    renderInputArea() {
        return `
            <div class="input-area">
                <div class="input-wrapper">
                    <input 
                        type="text" 
                        id="chatInput" 
                        class="chat-input" 
                        placeholder="Ask about flights, hotels, bookings..."
                        autocomplete="off"
                    >
                    <div class="input-actions">
                        <button class="action-btn" id="voiceBtn" title="Voice input">🎤</button>
                    </div>
                </div>
                <button class="send-btn" id="sendBtn" title="Send message">➤</button>
            </div>
        `;
    }

    setupEventListeners() {
        const sendBtn = document.getElementById('sendBtn');
        const chatInput = document.getElementById('chatInput');
        const clearBtn = document.getElementById('clearBtn');
        const voiceBtn = document.getElementById('voiceBtn');

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearChat());
        }

        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.startVoiceInput());
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        input.value = '';

        // Show loading
        this.isLoading = true;
        this.render();

        try {
            // Send to backend
            const response = await fetch(`${this.apiUrl}/api/search-flights`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    origin: 'BLR',
                    destination: 'DXB',
                    departure_date: '2025-12-10',
                    passengers: 1
                })
            });

            if (!response.ok) throw new Error('Failed to get response');

            const data = await response.json();

            // Simulate AI response (In production, integrate with Yellow.ai)
            const aiResponse = this.generateAIResponse(message, data);
            this.addMessage(aiResponse, 'ai');
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'ai');
        } finally {
            this.isLoading = false;
            this.render();
        }
    }

    generateAIResponse(userMessage, data) {
        const lowerMessage = userMessage.toLowerCase();

        if (lowerMessage.includes('flight') || lowerMessage.includes('book')) {
            if (data.outbound_flights && data.outbound_flights.length > 0) {
                const flight = data.outbound_flights[0];
                return `I found ${data.outbound_flights.length} flights for you! 
                
Top option: ${flight.airline} ${flight.flight_number}
Departure: ${flight.departure_time}
Price: ₹${flight.price}

Would you like to book this flight or see other options?`;
            }
        }

        if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
            return 'Hello! 👋 Welcome to Travel.ai. I can help you find flights, hotels, and make bookings. What are you looking for today?';
        }

        if (lowerMessage.includes('hotel')) {
            return 'I can help you find hotels! Where would you like to stay and for which dates?';
        }

        if (lowerMessage.includes('booking') || lowerMessage.includes('reserve')) {
            return 'To make a booking, just tell me your preferences for flights or hotels and I\'ll help you complete the reservation!';
        }

        return 'I understand you\'re looking for travel options. Could you please specify what you need? For example: "flights from Bengaluru to Dubai", or "hotels in Dubai"?';
    }

    addMessage(content, type) {
        const time = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });

        this.messages.push({ content, type, time });
        this.saveMessages();
    }

    saveMessages() {
        localStorage.setItem('chatMessages', JSON.stringify(this.messages));
    }

    loadMessages() {
        const saved = localStorage.getItem('chatMessages');
        this.messages = saved ? JSON.parse(saved) : [];
    }

    clearChat() {
        if (confirm('Clear all messages?')) {
            this.messages = [];
            this.saveMessages();
            this.render();
        }
    }

    startVoiceInput() {
        alert('Voice input will be integrated with Vapi in the next update!');
    }

    scrollToBottom() {
        setTimeout(() => {
            const container = document.querySelector('.messages-container');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }, 0);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

export default ChatInterface;
