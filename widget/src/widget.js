/**
 * Travel.ai Voice Widget with MCP Function Calling
 * Automatically detects flight queries and calls MCP backend
 */

class TravelVoiceWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: config.apiUrl || 'http://localhost:8080',
            vapiPublicKey: config.vapiPublicKey || '00ed1b9b-a752-4079-bc72-32986d840d52',
            vapiAssistantId: config.vapiAssistantId || 'e1c04a87-a8cf-4438-a91b-5888f69d1ef2',
            position: config.position || 'bottom-right',
            primaryColor: config.primaryColor || '#14B8A6',
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
        console.log('🎙️ Initializing Vapi SDK integration...');
        
        try {
            // SDK should already be loaded by index.html
            if (window.vapiSDK && typeof window.vapiSDK.run === 'function') {
                console.log('✅ Vapi SDK is available');
                console.log('📋 SDK methods:', Object.keys(window.vapiSDK));
                await this.initVapi();
                window.dispatchEvent(new CustomEvent('vapiReady'));
            } else {
                throw new Error('Vapi SDK not properly loaded');
            }
        } catch (error) {
            console.error('❌ Vapi initialization failed:', error);
            console.error('📋 window.vapiSDK:', window.vapiSDK);
            window.dispatchEvent(new CustomEvent('vapiError', { detail: error.message }));
            this.showError('Voice service unavailable. Please refresh the page.');
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
            <div class="widget-panel-footer" style="flex-direction: column; gap: 8px;">
                <div style="display: flex; width: 100%; gap: 12px; align-items: center;">
                    <div class="footer-input-wrapper">
                        <input 
                            type="text" 
                            class="footer-input" 
                            id="widgetTextInput"
                            placeholder="What can I help you?" 
                            onkeypress="if(event.key==='Enter'){window.myTripWidget.sendTextMessage()}"
                        />
                    </div>
                    <button class="footer-send-btn" onclick="window.myTripWidget.sendTextMessage()" title="Send message">
                        ➤
                    </button>
                </div>
                <div class="footer-powered-by">
                    <span>Powered by</span>
                    <span class="footer-logo">Travel.ai</span>
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
            console.log('🔧 Initializing Vapi SDK...');
            
            if (typeof window.vapiSDK === 'undefined') {
                throw new Error('Vapi SDK not loaded');
            }

            this.vapiClient = window.vapiSDK;
            this.vapiReady = true;
            
            console.log('✅ Vapi SDK ready');
            console.log('📋 Configuration:', {
                publicKey: this.config.vapiPublicKey.substring(0, 10) + '...',
                assistantId: this.config.vapiAssistantId
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
            console.log('📞 Starting voice call...');
            this.isListening = true;
            this.button.classList.add('active');
            this.updatePanelBody(this.getListeningStateHTML());
            
            // Use HTML SDK .run() method
            console.log('🎙️ Calling window.vapiSDK.run()...');
            console.log('📋 Configuration:', {
                publicKey: this.config.vapiPublicKey.substring(0, 10) + '...',
                assistantId: this.config.vapiAssistantId
            });
            
            // Start the call
            window.vapiSDK.run({
                apiKey: this.config.vapiPublicKey,
                assistant: this.config.vapiAssistantId
            });
            
            console.log('✅ Voice call started!');
            this.addMessage('🎙️ Voice call started - speak now! The AI will respond with voice.', 'system');
            
        } catch (error) {
            console.error('❌ Failed to start call:', error);
            this.showError(this.getErrorMessage(error));
            this.isListening = false;
            this.button.classList.remove('active');
            this.showMessages();
        }
    }


    async processUserMessage(message) {
        // All function calling is now handled by Vapi dashboard tools
        // No client-side intent detection or MCP calls needed
        console.log('✅ Message received - Vapi dashboard will handle tool calling');
        console.log('📝 User message:', message);
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
            
            // Stop Vapi call
            try {
                if (window.vapiSDK && window.vapiSDK.stop) {
                    window.vapiSDK.stop();
                    console.log('✅ Call stopped');
                }
            } catch (error) {
                console.error('❌ Error stopping call:', error);
            }
            
            this.onCallEnd();
        }
    }

    onCallStart() {
        this.isListening = true;
        this.button.classList.add('active');
        // Message already added in startVoiceCall
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
        
        // Always show messages if panel is open, even while listening
        if (this.isOpen) {
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
            // Scroll to bottom to show latest message
            setTimeout(() => {
                body.scrollTop = body.scrollHeight;
            }, 50);
        }
    }

    clearMessages() {
        this.messages = [];
        this.updatePanelBody(this.getInitialStateHTML());
    }

    sendTextMessage() {
        const input = document.getElementById('widgetTextInput');
        if (!input || !input.value.trim()) return;

        const message = input.value.trim();
        input.value = '';

        console.log('💬 Text message sent:', message);
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Process the message for MCP function calling
        this.processUserMessage(message);
        
        // Show a typing indicator
        this.addMessage('...', 'ai');
        
        // Simulate AI response (in real scenario, this would come from Vapi)
        setTimeout(() => {
            // Remove typing indicator
            if (this.messages[this.messages.length - 1].text === '...') {
                this.messages.pop();
            }
            
            // Add AI response
            this.addMessage('I received your message. How can I help you with your travel plans?', 'ai');
        }, 1000);
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

