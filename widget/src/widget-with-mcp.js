/**
 * Travel.ai Voice Widget with MCP Function Calling
 * Automatically detects flight queries and calls MCP backend
 */

class TravelVoiceWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: config.apiUrl || 'http://localhost:8080',
            vapiPublicKey: config.vapiPublicKey || '00ed1b9b-a752-4079-bc72-32986d840d52',
            vapiAssistantId: config.vapiAssistantId || '15f69bff-0ae1-4b2a-a4f3-aa84c350a73f',
            position: config.position || 'bottom-right',
            primaryColor: config.primaryColor || '#6366f1',
            ...config
        };

        this.isOpen = false;
        this.isListening = false;
        this.vapiClient = null;
        this.vapiReady = false;
        this.messages = [];
        this.lastUserMessage = '';
        this.processingFunction = false;
        
        this.init();
    }

    init() {
        this.createWidget();
        this.setupEventListeners();
        this.waitForVapiAndInit();
    }

    async waitForVapiAndInit() {
        console.log('🎙️ Waiting for Vapi SDK...');
        
        const waitForSDK = new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('SDK load timeout'));
            }, 20000);
            
            if (typeof window.vapiSDK !== 'undefined') {
                clearTimeout(timeout);
                resolve();
                return;
            }
            
            window.addEventListener('vapiSDKReady', () => {
                clearTimeout(timeout);
                resolve();
            }, { once: true });
            
            window.addEventListener('vapiSDKLoadFailed', () => {
                clearTimeout(timeout);
                reject(new Error('SDK failed to load'));
            }, { once: true });
        });
        
        try {
            await waitForSDK;
            console.log('✅ Vapi SDK detected');
            await this.initVapi();
            window.dispatchEvent(new CustomEvent('vapiReady'));
        } catch (error) {
            console.error('❌ Vapi SDK failed to load:', error);
            window.dispatchEvent(new CustomEvent('vapiError', { detail: error.message }));
            this.showError('Voice service unavailable. Please check your internet connection and refresh the page.');
        }
    }

    createWidget() {
        const button = document.createElement('button');
        button.className = 'mytrip-voice-widget-btn';
        button.innerHTML = '<span class="widget-btn-icon">🎙️</span>';
        button.onclick = () => this.togglePanel();
        button.title = 'Travel.ai Voice Assistant';
        
        const panel = document.createElement('div');
        panel.className = 'mytrip-voice-widget-panel';
        panel.innerHTML = this.getPanelHTML();

        document.body.appendChild(button);
        document.body.appendChild(panel);

        this.button = button;
        this.panel = panel;
    }

    getPanelHTML() {
        return `
            <div class="widget-panel-header">
                <div class="widget-header-content">
                    <div class="widget-header-icon">🎙️</div>
                    <div class="widget-header-text">
                        <h3>Travel.ai Assistant</h3>
                        <p>Your AI travel companion</p>
                    </div>
                </div>
                <button class="widget-close-btn" onclick="window.myTripWidget.togglePanel()">×</button>
            </div>
            <div class="widget-panel-body" id="widgetPanelBody">
                ${this.getInitialStateHTML()}
            </div>
            <div class="widget-panel-footer">
                <div class="footer-powered-by">
                    <span>Powered by</span>
                    <span class="footer-logo">Travel.ai × Vapi × MCP</span>
                </div>
            </div>
        `;
    }

    getInitialStateHTML() {
        return `
            <div class="widget-voice-status">
                <div class="voice-status-icon">✈️</div>
                <div class="voice-status-text">Ready to help!</div>
                <div class="voice-status-subtext">Ask me about flights, airports, or travel</div>
            </div>
            <div class="widget-action-buttons">
                <button class="widget-action-btn primary" onclick="window.myTripWidget.startVoiceCall()">
                    🎤 Start Voice Call
                </button>
            </div>
            <div class="widget-examples" style="margin-top: 20px; font-size: 12px; color: #666;">
                <div style="font-weight: bold; margin-bottom: 5px;">Try asking:</div>
                <div>• "Find flights from Mumbai to Dubai"</div>
                <div>• "What's the status of flight AI123?"</div>
                <div>• "Which airport is in Bangalore?"</div>
            </div>
        `;
    }

    getListeningStateHTML() {
        return `
            <div class="widget-voice-status">
                <div class="voice-status-icon listening">🎙️</div>
                <div class="voice-status-text">Listening...</div>
                <div class="voice-status-subtext">Speak now</div>
                <div class="voice-waveform">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
            </div>
            <div class="widget-action-buttons">
                <button class="widget-action-btn" onclick="window.myTripWidget.endVoiceCall()">
                    ❌ End Call
                </button>
            </div>
        `;
    }

    setupEventListeners() {
        window.myTripWidget = this;
    }

    async initVapi() {
        try {
            console.log('🔧 Initializing Vapi with MCP function calling...');
            
            if (typeof window.vapiSDK === 'undefined') {
                throw new Error('Vapi SDK not loaded');
            }

            this.vapiClient = window.vapiSDK;
            this.vapiReady = true;
            
            console.log('✅ Vapi SDK ready with MCP integration');
            console.log('📋 Configuration:', {
                publicKey: this.config.vapiPublicKey.substring(0, 10) + '...',
                assistantId: this.config.vapiAssistantId,
                mcpBackend: this.config.apiUrl
            });
            
        } catch (error) {
            console.error('❌ Failed to initialize Vapi:', error);
            this.vapiReady = false;
            throw error;
        }
    }

    togglePanel() {
        this.isOpen = !this.isOpen;
        this.panel.classList.toggle('open', this.isOpen);
        
        if (this.isOpen && this.messages.length === 0) {
            const welcomeMsg = this.vapiReady 
                ? 'Hi! I\'m your Travel.ai assistant. I can help you search for flights, check flight status, and find airports. Just ask me anything!'
                : 'Hi! Voice service is loading. Please wait a moment...';
            this.addMessage(welcomeMsg, 'ai');
        }
    }

    async startVoiceCall() {
        if (!this.vapiReady || !this.vapiClient) {
            this.showError('Voice service is still loading. Please wait a moment and try again.');
            return;
        }

        try {
            console.log('📞 Starting voice call with MCP function calling...');
            this.isListening = true;
            this.button.classList.add('active');
            this.updatePanelBody(this.getListeningStateHTML());

            // Start Vapi with speech recognition
            window.vapiSDK.run({
                apiKey: this.config.vapiPublicKey,
                assistant: this.config.vapiAssistantId,
                config: {
                    mode: 'voice'
                }
            });
            
            // Set up message listener for function calling
            this.setupMessageListener();
            
            console.log('✅ Voice call initiated with MCP integration!');
            this.onCallStart();
            
        } catch (error) {
            console.error('❌ Failed to start call:', error);
            this.showError(this.getErrorMessage(error));
            this.isListening = false;
            this.button.classList.remove('active');
            this.showMessages();
        }
    }

    setupMessageListener() {
        // Listen for speech recognition results
        if (window.vapiSDK && window.vapiSDK.on) {
            window.vapiSDK.on('message', async (message) => {
                console.log('📨 Message received:', message);
                
                // Check if this is user speech
                if (message.role === 'user' && message.content) {
                    this.lastUserMessage = message.content;
                    this.addMessage(message.content, 'user');
                    
                    // Process with function calling
                    await this.processUserMessage(message.content);
                }
            });
        }
    }

    async processUserMessage(message) {
        if (this.processingFunction) return;
        
        console.log('🧠 Processing user message for function calls:', message);
        
        // Detect intent and call appropriate function
        const intent = this.detectIntent(message);
        
        if (intent.type === 'search_flights') {
            await this.handleSearchFlights(intent.params);
        } else if (intent.type === 'flight_status') {
            await this.handleFlightStatus(intent.params);
        } else if (intent.type === 'search_airports') {
            await this.handleSearchAirports(intent.params);
        }
    }

    detectIntent(message) {
        const lowerMessage = message.toLowerCase();
        
        // Search flights intent
        if (lowerMessage.includes('flight') || lowerMessage.includes('fly') || 
            lowerMessage.includes('travel') || lowerMessage.includes('book')) {
            
            // Check for status query
            if (lowerMessage.includes('status') || lowerMessage.includes('track') ||
                lowerMessage.includes('check') && (lowerMessage.match(/[a-z]{2}\s?\d{3,4}/i))) {
                
                const flightNumber = this.extractFlightNumber(message);
                if (flightNumber) {
                    return {
                        type: 'flight_status',
                        params: { flight_number: flightNumber }
                    };
                }
            }
            
            // Search for flights
            const locations = this.extractLocations(message);
            if (locations.from || locations.to) {
                return {
                    type: 'search_flights',
                    params: locations
                };
            }
        }
        
        // Airport search intent
        if (lowerMessage.includes('airport') || lowerMessage.includes('which airport')) {
            const city = this.extractCity(message);
            if (city) {
                return {
                    type: 'search_airports',
                    params: { query: city }
                };
            }
        }
        
        return { type: 'none', params: {} };
    }

    extractLocations(message) {
        const locations = { from: null, to: null };
        
        // Common patterns
        const patterns = [
            /from\s+(\w+(?:\s+\w+)?)\s+to\s+(\w+(?:\s+\w+)?)/i,
            /(\w+(?:\s+\w+)?)\s+to\s+(\w+(?:\s+\w+)?)/i,
            /to\s+(\w+(?:\s+\w+)?)/i
        ];
        
        for (const pattern of patterns) {
            const match = message.match(pattern);
            if (match) {
                if (match.length === 3) {
                    locations.from = match[1].trim();
                    locations.to = match[2].trim();
                } else if (match.length === 2) {
                    locations.to = match[1].trim();
                }
                break;
            }
        }
        
        return locations;
    }

    extractFlightNumber(message) {
        const match = message.match(/([a-z]{2})\s?(\d{3,4})/i);
        if (match) {
            return match[1].toUpperCase() + match[2];
        }
        return null;
    }

    extractCity(message) {
        const match = message.match(/(?:airport\s+(?:in|at|for)\s+)?(\w+(?:\s+\w+)?)/i);
        if (match && match[1]) {
            return match[1].trim();
        }
        return null;
    }

    async handleSearchFlights(params) {
        if (!params.to) {
            this.addMessage('Which destination would you like to fly to?', 'ai');
            this.speakMessage('Which destination would you like to fly to?');
            return;
        }
        
        this.processingFunction = true;
        this.addMessage(`🔍 Searching flights to ${params.to}...`, 'system');
        
        try {
            console.log('📞 Calling MCP backend: search_flights', params);
            
            const response = await fetch(`${this.config.apiUrl}/api/functions/search_flights`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    parameters: {
                        from_airport: params.from || 'Current Location',
                        to_airport: params.to,
                        date: params.date
                    }
                })
            });
            
            const result = await response.json();
            console.log('✅ MCP response:', result);
            
            if (result.success && result.message) {
                this.addMessage(result.message, 'ai');
                this.speakMessage(result.message);
            } else {
                this.addMessage('I found some flights for you. Would you like more details?', 'ai');
                this.speakMessage('I found some flights for you. Would you like more details?');
            }
            
        } catch (error) {
            console.error('❌ Error calling MCP:', error);
            this.addMessage('I had trouble searching for flights. Please try again.', 'ai');
            this.speakMessage('I had trouble searching for flights. Please try again.');
        } finally {
            this.processingFunction = false;
        }
    }

    async handleFlightStatus(params) {
        this.processingFunction = true;
        this.addMessage(`🔍 Checking status of flight ${params.flight_number}...`, 'system');
        
        try {
            const response = await fetch(`${this.config.apiUrl}/api/functions/get_flight_status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    parameters: {
                        flight_number: params.flight_number,
                        date: params.date
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.message) {
                this.addMessage(result.message, 'ai');
                this.speakMessage(result.message);
            }
            
        } catch (error) {
            console.error('❌ Error checking flight status:', error);
            this.addMessage(`I couldn't check the status of flight ${params.flight_number}. Please check with your airline.`, 'ai');
        } finally {
            this.processingFunction = false;
        }
    }

    async handleSearchAirports(params) {
        this.processingFunction = true;
        this.addMessage(`🔍 Searching for airports in ${params.query}...`, 'system');
        
        try {
            const response = await fetch(`${this.config.apiUrl}/api/functions/search_airports`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    parameters: {
                        query: params.query
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.message) {
                this.addMessage(result.message, 'ai');
                this.speakMessage(result.message);
            }
            
        } catch (error) {
            console.error('❌ Error searching airports:', error);
            this.addMessage(`I couldn't find airports for ${params.query}.`, 'ai');
        } finally {
            this.processingFunction = false;
        }
    }

    speakMessage(text) {
        // Use browser's speech synthesis as fallback
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }

    endVoiceCall() {
        if (this.isListening) {
            console.log('🛑 Ending voice call...');
            this.onCallEnd();
        }
    }

    onCallStart() {
        this.isListening = true;
        this.button.classList.add('active');
        this.addMessage('🎙️ Voice call started - I\'m listening! Ask me about flights.', 'system');
    }

    onCallEnd() {
        this.isListening = false;
        this.button.classList.remove('active');
        this.showMessages();
        this.addMessage('Call ended. How else can I help you?', 'system');
    }

    addMessage(text, type) {
        const time = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });

        this.messages.push({ text, type, time });
        
        if (this.isOpen && !this.isListening) {
            this.showMessages();
        }
    }

    showMessages() {
        const messagesHTML = this.messages.map(msg => {
            let avatar = '🤖';
            let className = 'ai';
            
            if (msg.type === 'user') {
                avatar = '👤';
                className = 'user';
            } else if (msg.type === 'system') {
                avatar = 'ℹ️';
                className = 'ai';
            }

            return `
                <div class="widget-message ${className}">
                    <div class="message-avatar">${avatar}</div>
                    <div>
                        <div class="message-bubble">${this.escapeHtml(msg.text)}</div>
                        <div class="message-time">${msg.time}</div>
                    </div>
                </div>
            `;
        }).join('');

        const actionsHTML = `
            <div class="widget-action-buttons">
                <button class="widget-action-btn primary" onclick="window.myTripWidget.startVoiceCall()">
                    🎤 Talk Again
                </button>
                <button class="widget-action-btn" onclick="window.myTripWidget.clearMessages()">
                    🗑️ Clear
                </button>
            </div>
        `;

        this.updatePanelBody(messagesHTML + actionsHTML);
    }

    updatePanelBody(html) {
        const body = document.getElementById('widgetPanelBody');
        if (body) {
            body.innerHTML = html;
            body.scrollTop = body.scrollHeight;
        }
    }

    clearMessages() {
        this.messages = [];
        this.updatePanelBody(this.getInitialStateHTML());
    }

    showError(message) {
        console.error('⚠️ Widget Error:', message);
        this.addMessage(`⚠️ ${message}`, 'system');
        
        if (this.isOpen) {
            this.showMessages();
        }
    }

    getErrorMessage(error) {
        if (error.message) {
            if (error.message.includes('permission') || error.message.includes('Permission')) {
                return 'Microphone permission denied. Please allow microphone access and try again.';
            } else if (error.message.includes('secure') || error.message.includes('HTTPS')) {
                return 'Voice calls require HTTPS. Please use a secure connection.';
            } else if (error.message.includes('assistant')) {
                return 'Voice assistant not configured. Please check your settings.';
            } else {
                return `Error: ${error.message}`;
            }
        }
        return 'Failed to start voice call. Please try again.';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Auto-initialize widget when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
} else {
    initWidget();
}

function initWidget() {
    console.log('🚀 Initializing Travel.ai Voice Widget with MCP...');
    
    const widget = new TravelVoiceWidget({
        apiUrl: 'http://localhost:8080',
        vapiPublicKey: '00ed1b9b-a752-4079-bc72-32986d840d52',
        vapiAssistantId: '15f69bff-0ae1-4b2a-a4f3-aa84c350a73f'
    });

    window.myTripWidget = widget;
    
    console.log('🎙️ Travel.ai Voice Widget with MCP initialized!');
    console.log('✅ Features: Auto function calling, Flight search, Status check, Airport search');
}

export default TravelVoiceWidget;
export { TravelVoiceWidget };

