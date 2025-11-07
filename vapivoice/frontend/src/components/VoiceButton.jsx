import React, { useState, useEffect, useRef } from 'react';
import Vapi from '@vapi-ai/web';
import './VoiceButton.css';

const VoiceButton = ({ publicKey, assistantId }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [callId, setCallId] = useState(null); // ⭐ NEW: Track call ID for polling
  const vapiClientRef = useRef(null);
  const transcriptEndRef = useRef(null);
  const lastMessageRef = useRef({ content: '', timestamp: 0 });
  const processedMessagesRef = useRef(new Set());
  const pollIntervalRef = useRef(null); // ⭐ NEW: Track polling interval
  const muteStateRef = useRef(false); // ⭐ NEW: Track mute state in ref for accurate toggling
  const microphoneStreamRef = useRef(null); // ⭐ NEW: Store microphone stream for muting
  
  // ⭐ NEW: Trigger polling only when user asks for flights or hotels
  const [shouldPollFlights, setShouldPollFlights] = useState(false);
  const [shouldPollHotels, setShouldPollHotels] = useState(false);
  const [flightCardsDisplayed, setFlightCardsDisplayed] = useState(false); // ⭐ Track if cards already displayed
  const [hotelCardsDisplayed, setHotelCardsDisplayed] = useState(false); // ⭐ Track if hotel cards already displayed
  
  useEffect(() => {
    // Initialize Vapi client directly (no script loading needed)
    console.log('✅ Initializing Vapi SDK');
    
    // Set loading to false immediately so button appears
    setIsLoading(false);
    
    try {
      vapiClientRef.current = new Vapi(publicKey);
      
      // DEBUG: Listen to ALL events to see what Vapi sends
      const allEvents = [
        'call-start', 'call-end', 'speech-start', 'speech-end',
        'message', 'transcript', 'user-transcript', 'conversation-update',
        'function-call', 'function-call-result', 'tool-call', 'tool-call-result',
        'message-sent', 'assistant-message', 'error', 'volume-level'
      ];
      
      allEvents.forEach(eventName => {
        vapiClientRef.current.on(eventName, (data) => {
          if (eventName !== 'volume-level') { // Skip noisy volume events
            console.log(`🔔 Event: ${eventName}`, data ? JSON.stringify(data).substring(0, 200) : 'no data');
            
            // ⭐ CRITICAL: Check if THIS event has cards!
            if (data && typeof data === 'object') {
              if (data.cards && data.cards.length > 0) {
                console.log(`🎯 CARDS FOUND IN ${eventName.toUpperCase()} EVENT!`, data.cards.length, 'cards');
              }
              if (data.result && data.result.cards && data.result.cards.length > 0) {
                console.log(`🎯 CARDS FOUND IN ${eventName.toUpperCase()} EVENT (data.result.cards)!`, data.result.cards.length, 'cards');
              }
            }
          }
        });
      });
      
      // Set up event listeners
      vapiClientRef.current.on('call-start', () => {
        console.log('📞 Call started');
        setIsConnected(true);
        setCallId('latest'); // ⭐ Use 'latest' as backend caches with this key
          setShouldPollFlights(false); // ⭐ Reset flight polling flag
          setShouldPollHotels(false); // ⭐ Reset hotel polling flag
          setFlightCardsDisplayed(false); // ⭐ Reset cards displayed flag
          setHotelCardsDisplayed(false); // ⭐ Reset hotel cards displayed flag
          console.log('🔄 Call started - waiting for user to ask for flights or hotels');
        window.postMessage({ type: 'call-start' }, '*');
        
        console.log('✅ Call started - polling will begin when user asks...');
        
        // DEBUG: Log all available properties and methods on Vapi client
        console.log('🔍 Vapi client properties:', Object.keys(vapiClientRef.current));
        console.log('🔍 Vapi client._events:', vapiClientRef.current._events ? Object.keys(vapiClientRef.current._events) : 'no _events');
      });
      
      vapiClientRef.current.on('call-end', () => {
        console.log('📞 Call ended - Preparing cleanup...');
        console.log('  ⏸️  Waiting 3 seconds for cards to render before cleanup...');
        
        // ⭐ CRITICAL FIX: Wait 3 seconds before cleanup
        // This gives time for:
        // 1. Polling to fetch cards from backend
        // 2. Frontend to render the cards
        // 3. Cards to display before session cleanup
        
        setTimeout(() => {
          console.log('📞 Call ended - Now cleaning up after card display...');
        console.log('  - Stopping polling...');
        
        // Stop polling interval
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          console.log('  ✅ Polling stopped');
        }
        
        console.log('  - Resetting states...');
        setIsConnected(false);
        setIsListening(false);
        setIsAssistantSpeaking(false);
        setIsMuted(false);
          muteStateRef.current = false;
        setCallId(null);
        setShouldPollFlights(false);
        setShouldPollHotels(false);
        setFlightCardsDisplayed(false); // ⭐ Reset cards displayed flag
        setHotelCardsDisplayed(false); // ⭐ Reset hotel cards displayed flag
        console.log('  ✅ All states reset');
        
        window.postMessage({ type: 'call-end' }, '*');
        console.log('📞 Call ended - Cleanup complete');
        }, 3000); // 3 second delay for card rendering
      });
      
      vapiClientRef.current.on('speech-start', () => {
        console.log('🎤 Speech started');
        // Will be clarified by transcript event - don't set flags yet
      });
      
      vapiClientRef.current.on('speech-end', () => {
        console.log('🎤 Speech ended');
        // Will be clarified by transcript event - don't set flags yet
      });

      // Capture user's spoken text
      // NOTE: Transcripts are coming through 'message' event instead, not 'user-transcript'
      vapiClientRef.current.on('user-transcript', (data) => {
        console.log('👤 user-transcript event (not used - transcripts via message event):', data);
        // Transcripts are handled by message event handler instead
        return;
      });
      
      // Listen for transcript events (real-time AI responses)
      // NOTE: Not being used - transcripts come through 'message' event instead
      vapiClientRef.current.on('transcript', (data) => {
        console.log('📝 transcript event (not used - transcripts via message event):', data);
        // Transcripts are handled by message event handler instead
        return;
      });
      
      // Optionally listen for message events for metadata only (not for transcript)
      vapiClientRef.current.on('message', (message) => {
        console.log('💬 Vapi message event full object:', JSON.stringify(message, null, 2));
        console.log('  - message.type:', message.type);
        console.log('  - message.cards:', message.cards);
        console.log('  - message.content:', message.content);
        console.log('  - message.result:', message.result);
        console.log('  - message.text:', message.text);
        console.log('  - message.functionCall:', message.functionCall);
        console.log('  - message.toolCalls:', message.toolCalls);
        console.log('  - message.toolCallList:', message.toolCallList);
        console.log('  - Object keys:', Object.keys(message).join(', '));
        
        // Check for cards in nested structures
        if (message.result) {
          console.log('  🔍 Checking message.result for cards...');
          console.log('    - message.result.cards:', message.result.cards);
          console.log('    - message.result type:', typeof message.result);
          if (typeof message.result === 'string') {
            try {
              const parsed = JSON.parse(message.result);
              console.log('    - Parsed message.result:', parsed);
              console.log('    - Parsed.cards:', parsed.cards);
            } catch (e) {
              console.log('    - message.result is not JSON');
            }
          }
        }
        
        if (message.content) {
          console.log('  🔍 Checking message.content for cards...');
          if (typeof message.content === 'string') {
            try {
              const parsed = JSON.parse(message.content);
              console.log('    - Parsed message.content:', parsed);
              console.log('    - Parsed.cards:', parsed.cards);
            } catch (e) {
              console.log('    - message.content is not JSON');
            }
          } else if (typeof message.content === 'object') {
            console.log('    - message.content.cards:', message.content.cards);
          }
        }
        
        // Handle transcript messages from the message event
        if (message.type === 'transcript' && message.transcript) {
          console.log(`📝 TRANSCRIPT from message event - role: ${message.role}, type: ${message.transcriptType}, text: ${message.transcript.substring(0, 50)}`);
          
          const text = message.transcript;
          const messageRole = message.role || 'assistant';
          const isFinal = message.transcriptType === 'final';
          
          // ⭐ NEW: Check for keywords in FINAL transcript from AI (for polling trigger)
          if (isFinal && messageRole === 'assistant') {
            const lowerText = text.toLowerCase();
            console.log(`\n✨✨✨ CHECKING FINAL TRANSCRIPT FOR KEYWORDS ✨✨✨`);
            console.log(`    Text: "${text.substring(0, 150)}"`);
            console.log(`    Lowercase: "${lowerText.substring(0, 150)}"`);
            
            // Check for flight-related keywords
            if (lowerText.includes('flight options') || 
                lowerText.includes('here are your flights') || 
                lowerText.includes('found several flights') ||
                lowerText.includes('found flights') ||
                (lowerText.includes('found') && lowerText.includes('flight'))) {
              console.log('✈️✈️✈️ FOUND FLIGHT KEYWORD IN TRANSCRIPT - TRIGGERING POLLING! ✈️✈️✈️');
              setShouldPollFlights(true);
            }
            
            // Check for hotel-related keywords
            if (lowerText.includes('hotel options') || 
                lowerText.includes('here are your hotels') || 
                lowerText.includes('found hotels') ||
                lowerText.includes('accommodation')) {
              console.log('🏨🏨🏨 FOUND HOTEL KEYWORD IN TRANSCRIPT - TRIGGERING POLLING! 🏨🏨🏨');
              setShouldPollHotels(true);
            }
          }
          
          // Update listening/speaking states
          if (messageRole === 'user') {
            setIsListening(true);
            setIsAssistantSpeaking(false);
          } else {
            setIsListening(false);
            setIsAssistantSpeaking(true);
          }
          
          // Add to transcript
          setTranscript(prev => {
            // For partial transcripts, update the last message of same role
            const lastMsg = prev[prev.length - 1];
            if (!isFinal && lastMsg && lastMsg.role === messageRole && !lastMsg.final) {
              console.log('🔄 Updating partial transcript from message event');
              const updated = [...prev.slice(0, -1), {
                ...lastMsg,
                content: text,
                final: false
              }];
              console.log('📊 Transcript after update:', updated.length, 'messages');
              return updated;
            } else if (isFinal) {
              // Check for duplicate
              const isDuplicate = prev.some(msg => 
                msg.role === messageRole && 
                msg.content === text && 
                msg.final === true
              );
              
              if (isDuplicate) {
                console.log('⚠️ Final transcript duplicate, skipping');
                return prev;
              }
              
              // Replace partial or add new final
              if (lastMsg && lastMsg.role === messageRole && !lastMsg.final) {
                console.log('✅ Converting partial to final from message event');
                const updated = [...prev.slice(0, -1), {
                  ...lastMsg,
                  content: text,
                  final: true,
                  timestamp: new Date()
                }];
                console.log('📊 Transcript after convert:', updated.length, 'messages');
                
                // ⭐ NEW: Detect if user asked for flights or hotels (when converting partial to final)
                // DISABLED: We now wait for function response instead of polling on keywords
                /*
                if (messageRole === 'user' && isFinal) {
                  const lowerText = text.toLowerCase();
                  if (lowerText.includes('flight') || lowerText.includes('search flight') || lowerText.includes('find flight') || lowerText.includes('from') || lowerText.includes('to')) {
                    console.log('✈️ USER ASKED FOR FLIGHTS - Starting flight polling!');
                    setShouldPollFlights(true);
                  }
                  if (lowerText.includes('hotel') || lowerText.includes('search hotel') || lowerText.includes('find hotel') || lowerText.includes('accommodation')) {
                    console.log('🏨 USER ASKED FOR HOTELS - Starting hotel polling!');
                    setShouldPollHotels(true);
                  }
                }
                */
                
                return updated;
              } else {
                console.log('✅ Adding new final transcript from message event');
                const updated = [...prev, {
                  role: messageRole,
                  content: text,
                  timestamp: new Date(),
                  final: true
                }];
                console.log('📊 Transcript after add:', updated.length, 'messages');
                
                // ⭐ NEW: Detect if user asked for flights or hotels
                // DISABLED: We now wait for function response instead of polling on keywords
                /*
                if (messageRole === 'user' && isFinal) {
                  const lowerText = text.toLowerCase();
                  if (lowerText.includes('flight') || lowerText.includes('search flight') || lowerText.includes('find flight') || lowerText.includes('from') || lowerText.includes('to')) {
                    console.log('✈️ USER ASKED FOR FLIGHTS - Starting flight polling!');
                    setShouldPollFlights(true);
                  }
                  if (lowerText.includes('hotel') || lowerText.includes('search hotel') || lowerText.includes('find hotel') || lowerText.includes('accommodation')) {
                    console.log('🏨 USER ASKED FOR HOTELS - Starting hotel polling!');
                    setShouldPollHotels(true);
                  }
                }
                */
                
                return updated;
              }
            } else {
              // Add new partial
              console.log('➕ Adding partial transcript from message event');
              const updated = [...prev, {
                role: messageRole,
                content: text,
                timestamp: new Date(),
                final: false
              }];
              console.log('📊 Transcript after add partial:', updated.length, 'messages');
              return updated;
            }
          });
        }
        
        // Check for flight cards in the message
        if (message.cards && message.cards.length > 0) {
          console.log('✈️ Flight cards detected:', message.cards.length);
          
          // Display each flight card in the transcript
          message.cards.forEach((card, index) => {
            const flightHtml = `
              <div class="flight-card-widget" style="background:#1a1a1a;border:2px solid #14B8A6;border-radius:12px;padding:16px;margin-top:12px;font-family:system-ui;width:100%;max-width:500px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                  <div style="font-size:18px;font-weight:600;color:#14B8A6">
                    ${card.title || 'Flight'}
                  </div>
                  <div style="font-size:20px;font-weight:700;color:#fff">
                    ${card.footer ? card.footer.split('|')[1]?.trim() || '---' : '---'}
                  </div>
                </div>
                <div style="color:#aaa;margin-bottom:12px">
                  <div><strong style="color:#fff">${card.subtitle || 'N/A'}</strong></div>
                  <div style="font-size:14px;margin-top:8px">${card.footer || ''}</div>
                </div>
                ${card.buttons && card.buttons.length > 0 ? `
                  <a href="${card.buttons[0].url}" 
                     target="_blank" 
                     style="display:inline-block;background:#14B8A6;color:#1a1a1a;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">
                    ${card.buttons[0].text || 'View'}
                  </a>
                ` : ''}
              </div>
            `;
            
            setTranscript(prev => [...prev, {
              role: 'assistant',
              content: flightHtml,
              timestamp: new Date(),
              final: true,
              isHTML: true
            }]);
          });
        }
        
        // Forward to parent app for flight cards only
        if (message.type === 'function-call' || message.functionCall) {
          const functionName = message.functionCall?.name || message.function?.name || '';
          console.log('🔧 FUNCTION CALL detected:', functionName);
          
          // ⭐ CRITICAL: Trigger polling when search_flights function is called
          if (functionName === 'search_flights') {
            console.log('✈️✈️✈️ SEARCH_FLIGHTS FUNCTION CALLED - STARTING POLLING! ✈️✈️✈️');
            setShouldPollFlights(true);
          }
          if (functionName === 'search_hotels') {
            console.log('🏨🏨🏨 SEARCH_HOTELS FUNCTION CALLED - STARTING POLLING! 🏨🏨🏨');
            setShouldPollHotels(true);
          }
          
          window.postMessage({
            type: 'vapi-function-call',
            message: message
          }, '*');
        }
      });
      
      // Listen for conversation updates which might contain function results with flight cards
      vapiClientRef.current.on('conversation-update', (conversation) => {
        console.log('🎯🎯🎯 ===== CONVERSATION UPDATE EVENT FIRED ===== 🎯🎯🎯');
        console.log('💬 Full conversation object:', JSON.stringify(conversation, null, 2).substring(0, 2000));
        console.log('  - Has messages:', conversation?.messages?.length || 0);
        console.log('  - Conversation keys:', Object.keys(conversation || {}).join(', '));
        
        if (conversation?.messages) {
          console.log(`\n📨 Processing ${conversation.messages.length} messages...`);
          conversation.messages.forEach((msg, idx) => {
            console.log(`\n📨 ===== Message ${idx} ===== `);
            console.log(`    Type: ${msg.type}`);
            console.log(`    Role: ${msg.role}`);
            console.log(`    Keys: ${Object.keys(msg).join(', ')}`);
            console.log(`    Has result: ${!!msg.result}`);
            console.log(`    Has cards: ${!!msg.cards}`);
            console.log(`    Has content: ${!!msg.content}`);
            
            // Log full message for debugging
            console.log(`    Full Message ${idx}:`, JSON.stringify(msg).substring(0, 1000));
            
            // ⭐ NEW: Trigger polling when AI says "Here are your flight/hotel options"
            // This ensures cards are fetched from backend cache
            if (msg.role === 'assistant' && msg.content) {
              console.log(`\n✅ Found assistant message! Content length: ${msg.content.length}`);
              console.log(`    First 150 chars: "${msg.content.substring(0, 150)}"`);
              
              const lowerContent = msg.content.toLowerCase();
              console.log(`    Lowercase version: "${lowerContent.substring(0, 150)}"`);
              
              // More flexible detection for flight-related messages
              if (lowerContent.includes('flight options') || 
                  lowerContent.includes('here are your flights') || 
                  lowerContent.includes('found several flights') ||
                  lowerContent.includes('found flights') ||
                  lowerContent.includes('search is for') ||
                  (lowerContent.includes('found') && lowerContent.includes('flight'))) {
                console.log('✈️✈️✈️ AI mentioned flight options - Starting polling! ✈️✈️✈️');
                console.log('   Message content:', msg.content.substring(0, 100));
                setShouldPollFlights(true);
              }
              // More flexible detection for hotel-related messages
              if (lowerContent.includes('hotel options') || 
                  lowerContent.includes('here are your hotels') || 
                  lowerContent.includes('found hotels') ||
                  lowerContent.includes('accommodation')) {
                console.log('🏨🏨🏨 AI mentioned hotel options - Starting polling! 🏨🏨🏨');
                console.log('   Message content:', msg.content.substring(0, 100));
                setShouldPollHotels(true);
              }
            } else if (msg.role === 'assistant') {
              console.log(`    ⚠️ Assistant message but NO CONTENT! msg.content is:`, msg.content);
            }
            
            // Check if this message has cards directly (msg.cards)
            // ⭐ REMOVED: Don't display cards here - only use backend polling to prevent duplicates
            // Cards will be displayed via backend polling after all details are collected
            if (msg.cards && msg.cards.length > 0) {
              console.log(`    ✅ CARDS FOUND IN MESSAGE (will be displayed via polling):`, msg.cards.length, 'cards');
              // Don't display here - let backend polling handle it to prevent duplicates
            }
            
            // Check for tool results which contain flight card data
            if (msg.role === 'tool' || msg.type === 'tool-result' || msg.type === 'function-result') {
              console.log(`    💬 Tool/Function Result message found:`, msg.content?.substring(0, 100));
              
              try {
                // Try to parse the content as JSON (it contains the function response)
                const toolResult = typeof msg.content === 'string' ? JSON.parse(msg.content) : msg.content;
                
                if (toolResult?.cards && toolResult.cards.length > 0) {
                  console.log(`    ✈️ FLIGHT CARDS FOUND IN TOOL RESULT:`, toolResult.cards.length, 'cards');
                  
                  // Display each flight card
                  toolResult.cards.forEach((card, cardIdx) => {
                    console.log(`      Card ${cardIdx}:`, card.title);
                    const flightHtml = `
                      <div class="flight-card-widget" style="background:#1a1a1a;border:2px solid #14B8A6;border-radius:12px;padding:16px;margin-top:12px;font-family:system-ui;width:100%;max-width:500px">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                          <div style="font-size:18px;font-weight:600;color:#14B8A6">
                            ${card.title || 'Flight'}
                          </div>
                          <div style="font-size:20px;font-weight:700;color:#fff">
                            ${card.footer ? card.footer.split('|')[1]?.trim() || '---' : '---'}
                          </div>
                        </div>
                        <div style="color:#aaa;margin-bottom:12px">
                          <div><strong style="color:#fff">${card.subtitle || 'N/A'}</strong></div>
                          <div style="font-size:14px;margin-top:8px">${card.footer || ''}</div>
                        </div>
                        ${card.buttons && card.buttons.length > 0 ? `
                          <a href="${card.buttons[0].url}" 
                             target="_blank" 
                             style="display:inline-block;background:#14B8A6;color:#1a1a1a;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">
                            ${card.buttons[0].text || 'View'}
                          </a>
                        ` : ''}
                      </div>
                    `;
                    
                    setTranscript(prev => [...prev, {
                      role: 'assistant',
                      content: flightHtml,
                      timestamp: new Date(),
                      final: true,
                      isHTML: true
                    }]);
                  });
                }
              } catch (parseError) {
                console.log(`    ⚠️ Could not parse tool result as JSON:`, parseError);
              }
            }
            
            // ✅ CRITICAL: Check for cards in msg.result (Vapi Custom Tool response format)
            if (msg.result && typeof msg.result === 'object') {
              console.log(`    🔍 Checking msg.result for cards...`);
              console.log(`      - msg.result type:`, typeof msg.result);
              console.log(`      - msg.result.cards:`, msg.result.cards ? `${msg.result.cards.length} cards` : 'undefined');
              
              if (msg.result.cards && msg.result.cards.length > 0) {
                console.log(`    ✈️ FLIGHT CARDS FOUND IN msg.result.cards (will be displayed via polling):`, msg.result.cards.length, 'cards');
                // ⭐ REMOVED: Don't display cards here - only use backend polling to prevent duplicates
                // Cards will be displayed via backend polling after all details are collected
              }
            }
            
            if (msg.result) {
              console.log(`      ✈️ Result found:`, typeof msg.result === 'string' ? msg.result.substring(0, 100) : 'object');
            }
            if (msg.cards) {
              console.log(`      ✈️ Cards found:`, msg.cards.length, 'cards');
            }
          });
        }
      });
      
      // Listen for function call results which might contain the flight cards
      vapiClientRef.current.on('function-call-result', (result) => {
        console.log('🔧 FUNCTION CALL RESULT event:', JSON.stringify(result, null, 2));
        console.log('  - Result keys:', Object.keys(result).join(', '));
        
        // ⭐ CRITICAL: Trigger polling when search_flights function completes
        const functionName = result?.functionCall?.name || result?.function?.name || result?.name || '';
        if (functionName === 'search_flights') {
          console.log('✈️✈️✈️ SEARCH_FLIGHTS FUNCTION RESULT - STARTING POLLING! ✈️✈️✈️');
          setShouldPollFlights(true);
        }
        if (functionName === 'search_hotels') {
          console.log('🏨🏨🏨 SEARCH_HOTELS FUNCTION RESULT - STARTING POLLING! 🏨🏨🏨');
          setShouldPollHotels(true);
        }
        
        if (result?.result) {
          console.log('  - Has result.result:', typeof result.result);
        }
        
        if (result?.cards) {
          console.log('  ✈️ Cards found in function result (will be displayed via polling):', result.cards.length);
          // ⭐ REMOVED: Don't display cards here - only use backend polling to prevent duplicates
          // Cards will be displayed via backend polling after all details are collected
        }
      });
      
      // Listen for message-sent event (Vapi's standard way to send assistant messages with cards)
      vapiClientRef.current.on('message-sent', (message) => {
        console.log('📤 MESSAGE SENT event:', JSON.stringify(message, null, 2));
        console.log('  - Message keys:', Object.keys(message).join(', '));
        
        if (message?.cards && message.cards.length > 0) {
          console.log('✈️ FLIGHT CARDS FOUND IN MESSAGE-SENT (will be displayed via polling):', message.cards.length, 'cards');
          // ⭐ REMOVED: Don't display cards here - only use backend polling to prevent duplicates
          // Cards will be displayed via backend polling after all details are collected
        }
      });
      
      vapiClientRef.current.on('error', async (error) => {
        console.group('❌ Vapi error details (global handler)');
        console.log('Status:', error.status || error.statusCode);
        console.log('Type:', error.type);
        console.log('Message:', error.message);
        console.log('Body:', error.body);
        
        // Extract real server response - try multiple methods
        let serverResponse = null;
        try {
          // Method 1: error.error is a Response object
          if (error.error && error.error.json) {
            try {
              const jsonData = await error.error.json();
              serverResponse = JSON.stringify(jsonData, null, 2);
              console.log('Server Response (from error.error.json):', serverResponse);
            } catch (e) {
              console.log('Could not parse error.error as JSON:', e);
            }
          }
          
          // Method 2: error.error has text()
          if (!serverResponse && error.error && error.error.text) {
            try {
              serverResponse = await error.error.text();
              console.log('Server Response (from error.error.text):', serverResponse);
            } catch (e) {
              console.log('Could not get error.error.text():', e);
            }
          }
          
          // Method 3: Original method
          if (!serverResponse && error.response?.text) {
            serverResponse = await error.response.text();
            console.log('Server Response (from error.response):', serverResponse);
          } else if (!serverResponse && error.response?.json) {
            serverResponse = JSON.stringify(await error.response.json());
            console.log('Server Response (JSON):', serverResponse);
          }
        } catch (e) {
          console.log('Could not extract response:', e);
        }
        
        console.log('Full error object:', error);
        console.groupEnd();
        
        // Try to extract the actual error message
        const errorMsg = serverResponse ||
                        error.message || 
                        error.error?.message || 
                        error.body?.error || 
                        error.data?.error ||
                        'Unknown error';
        
        console.error('🚨 Final error message:', errorMsg);
        
        // Show user-friendly alert
        if (errorMsg && !error.type?.includes('microphone')) {
          alert(`Vapi Error: ${errorMsg}\n\nPlease check:\n1. Assistant ID is correct\n2. Assistant is published in Vapi dashboard\n3. Assistant has model and voice configured\n4. Public key matches workspace`);
        }
      });
      
      console.log('✅ Vapi SDK initialized successfully');
      // Loading already set to false above
      
      // Hide any default Vapi UI elements that might appear
      setTimeout(() => {
        const style = document.createElement('style');
        style.id = 'vapi-ui-override';
        style.innerHTML = `
          /* Force hide any Vapi default floating buttons */
          [class*="vapi-"] button[class*="record"],
          [class*="vapi-"] button[class*="mic"],
          [class*="vapi-"] button[style*="border-radius: 50%"],
          [class*="vapi-"] [class*="floating"],
          div[style*="position: fixed"][style*="z-index"][style*="bottom"] > button[style*="50%"] {
            display: none !important;
            opacity: 0 !important;
            pointer-events: none !important;
          }
        `;
        if (!document.getElementById('vapi-ui-override')) {
          document.head.appendChild(style);
        }
        console.log('🎨 Vapi UI override styles applied');
      }, 1000);
      
    } catch (error) {
      console.error('❌ Failed to initialize Vapi SDK:', error);
      // Loading already set to false above
    }

    return () => {
      if (vapiClientRef.current && isConnected) {
        vapiClientRef.current.stop();
      }
    };
  }, [publicKey, isConnected]);

  // Debug: Log transcript changes
  useEffect(() => {
    console.log('📋 Transcript updated. Total messages:', transcript.length);
    transcript.forEach((msg, idx) => {
      console.log(`  ${idx + 1}. [${msg.role}]:`, msg.content.substring(0, 50) + '...');
    });
  }, [transcript]);

  // Auto-scroll to bottom when transcript updates
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcript]);

  // ⭐ NEW: Poll backend API for flight cards
  useEffect(() => {
    if (isConnected && callId && shouldPollFlights) {
      console.log(`🔄 Starting backend polling for call_id: ${callId || 'latest'}`);
      console.log(`⏱️  Will poll every 2 seconds for up to 90 seconds (45 attempts)`);
      let pollCount = 0;
      const maxPolls = 45; // Poll for up to 90 seconds (increased for testing)
      
      pollIntervalRef.current = setInterval(async () => {
        pollCount++;
        const pollCallId = callId || 'latest';
        console.log(`🔄 Backend poll attempt ${pollCount}/${maxPolls} for call_id: ${pollCallId}`);
        
        if (pollCount > maxPolls) {
          console.log('');
          console.log('⏹️⏹️⏹️ POLLING TIMEOUT ⏹️⏹️⏹️');
          console.log(`Stopped polling after ${maxPolls} attempts (90 seconds)`);
          console.log('No flight cards were found in backend cache');
          console.log('This means the backend never received the search_flights call from Vapi');
          console.log('Check: Vapi webhook URL configuration');
          console.log('');
          clearInterval(pollIntervalRef.current);
          return;
        }
        
        try {
          const response = await fetch(`http://localhost:4000/api/flight-cards/${pollCallId}`);
          const data = await response.json();
          
          console.log(`📡 Backend response:`, data);
          
          if (data.success && data.cards && data.cards.length > 0) {
            console.log('');
            console.log('🎯🎯🎯 CARDS FOUND VIA BACKEND POLLING! 🎯🎯🎯');
            console.log(`📦 Found ${data.cards.length} flight cards in backend cache`);
            console.log(`⏱️  Took ${pollCount} poll attempts (${pollCount * 2} seconds)`);
            console.log('');
            
            // ⭐ CRITICAL: Only display cards ONCE
            if (flightCardsDisplayed) {
              console.log('⚠️ Flight cards already displayed in widget - skipping duplicate display');
            clearInterval(pollIntervalRef.current);
              setShouldPollFlights(false);
              return;
            }
            
            console.log('✅✅✅ DISPLAYING FLIGHT CARDS IN WIDGET NOW! ✅✅✅');
            console.log('Cards will appear in the chat widget!');
            console.log('');
            clearInterval(pollIntervalRef.current);
            setShouldPollFlights(false); // ⭐ Stop polling after cards found
            setFlightCardsDisplayed(true); // ⭐ Mark cards as displayed
            
            // ⭐ DISPLAY FLIGHT CARDS IN WIDGET (not App.jsx)
            data.cards.forEach((card, idx) => {
              console.log(`  ✈️ Rendering flight card ${idx + 1}/${data.cards.length} in widget:`, card.title);
              
              // Create HTML for flight card widget (simple original style)
              const flightHtml = `
                <div class="flight-card-widget" style="background:#1a1a1a;border:2px solid #14B8A6;border-radius:12px;padding:16px;margin-top:12px;font-family:system-ui;width:100%;max-width:500px">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                    <div style="font-size:18px;font-weight:600;color:#14B8A6">
                      ${card.title || 'Flight'}
                    </div>
                    <div style="font-size:20px;font-weight:700;color:#fff">
                      ${card.footer ? (card.footer.match(/₹([\d,]+)/)?.[0] || '---') : '---'}
                    </div>
                  </div>
                  <div style="color:#aaa;margin-bottom:12px">
                    <div><strong style="color:#fff">${card.subtitle || 'N/A'}</strong></div>
                    <div style="font-size:14px;margin-top:8px;color:#ddd">${card.footer || ''}</div>
                  </div>
                  ${card.buttons && card.buttons.length > 0 ? `
                    <a href="${card.buttons[0].url}" 
                       target="_blank" 
                       style="display:inline-block;background:#14B8A6;color:#1a1a1a;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">
                      ${card.buttons[0].text || 'Book Now'}
                    </a>
                  ` : ''}
                </div>
              `;
              
              // Add card to widget transcript
              setTranscript(prev => [...prev, {
                role: 'assistant',
                content: flightHtml,
                timestamp: new Date(),
                final: true,
                isHTML: true
              }]);
            });
            
            // Also add a summary message
            setTranscript(prev => [...prev, {
              role: 'assistant',
              content: `✅ Found ${data.cards.length} flight options above. Please review and let me know which flight you'd like to book.`,
              timestamp: new Date(),
              final: true
            }]);
          }
        } catch (error) {
          console.log('⚠️ Error polling backend:', error);
        }
      }, 2000); // Poll every 2 seconds
      
      // Cleanup on unmount or when call ends
      return () => {
        if (pollIntervalRef.current) {
          console.log('🛑 Cleaning up backend polling');
          clearInterval(pollIntervalRef.current);
        }
      };
    }
  }, [isConnected, callId, shouldPollFlights, flightCardsDisplayed]); // ⭐ Added flightCardsDisplayed to dependencies

  // ⭐ NEW: Poll backend API for HOTEL cards
  useEffect(() => {
    if (isConnected && callId && shouldPollHotels) {
      console.log(`🏨 Starting backend polling for hotel cards with call_id: ${callId || 'latest'}`);
      console.log(`⏱️  Will poll every 2 seconds for up to 90 seconds (45 attempts)`);
      let pollCount = 0;
      const maxPolls = 45;
      
      const hotelPollInterval = setInterval(async () => {
        pollCount++;
        const pollCallId = callId || 'latest';
        console.log(`🏨 Hotel poll attempt ${pollCount}/${maxPolls} for call_id: ${pollCallId}`);
        
        if (pollCount > maxPolls) {
          console.log('');
          console.log('⏹️⏹️⏹️ HOTEL POLLING TIMEOUT ⏹️⏹️⏹️');
          console.log(`Stopped polling after ${maxPolls} attempts (90 seconds)`);
          console.log('No hotel cards were found in backend cache');
          console.log('This means the backend never received the search_hotels call from Vapi');
          console.log('');
          clearInterval(hotelPollInterval);
          return;
        }
        
        try {
          const response = await fetch(`http://localhost:4000/api/hotel-cards/${pollCallId}`);
          const data = await response.json();
          
          console.log(`🏨 Hotel backend response:`, data);
          
          if (data.success && data.cards && data.cards.length > 0) {
            console.log('');
            console.log('🏨🏨🏨 HOTEL CARDS FOUND VIA BACKEND POLLING! 🏨🏨🏨');
            console.log(`📦 Found ${data.cards.length} hotel cards in backend cache`);
            console.log(`⏱️  Took ${pollCount} poll attempts (${pollCount * 2} seconds)`);
            console.log('');
            console.log('✅✅✅ DISPLAYING HOTEL CARDS NOW! ✅✅✅');
            console.log('Cards will appear immediately!');
            console.log('');
            clearInterval(hotelPollInterval);
            setShouldPollHotels(false); // ⭐ Stop polling after cards found
            
            // Render each hotel card (simple original style)
            data.cards.forEach((card, idx) => {
              console.log(`  🏨 Rendering hotel card ${idx + 1}/${data.cards.length}:`, card.title);
              
              const hotelHtml = `
                <div class="hotel-card-widget" style="background:#1a1a1a;border:2px solid #F59E0B;border-radius:12px;padding:16px;margin-top:12px;font-family:system-ui;width:100%;max-width:500px">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                    <div style="font-size:18px;font-weight:600;color:#F59E0B">${card.title || 'Hotel'}</div>
                  </div>
                  <div style="color:#aaa;margin-bottom:12px">
                    <div><strong style="color:#fff">${card.subtitle || 'N/A'}</strong></div>
                    <div style="font-size:14px;margin-top:8px;color:#ddd">${card.footer || ''}</div>
                  </div>
                  ${card.buttons && card.buttons.length > 0 ? `
                    <a href="${card.buttons[0].url}" target="_blank" 
                       style="display:inline-block;background:#F59E0B;color:#1a1a1a;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">
                      ${card.buttons[0].text || 'View'}
                    </a>
                  ` : ''}
                </div>
              `;
              
              setTranscript(prev => [...prev, {
                role: 'assistant',
                content: hotelHtml,
                timestamp: new Date(),
                final: true,
                isHTML: true
              }]);
            });
          }
        } catch (error) {
          console.log('⚠️ Error polling hotel backend:', error);
        }
      }, 2000); // Poll every 2 seconds
      
      // Cleanup on unmount or when call ends
      return () => {
        if (hotelPollInterval) {
          console.log('🛑 Cleaning up hotel backend polling');
          clearInterval(hotelPollInterval);
        }
      };
    }
  }, [isConnected, callId, shouldPollHotels]);

  // Expose function to inject flight cards programmatically
  useEffect(() => {
    // Global function to inject flight cards from anywhere
    window.injectFlightCard = (flightData) => {
      console.log('✈️ Injecting flight card:', flightData);
      
      const html = `
        <div class="flight-card-widget" style="background:#1a1a1a;border:1px solid #14B8A6;border-radius:12px;padding:16px;margin-top:12px;font-family:system-ui">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div style="font-size:18px;font-weight:600;color:#14B8A6">
              ✈️ ${flightData.from || flightData.origin} → ${flightData.to || flightData.destination}
            </div>
            <div style="font-size:20px;font-weight:700;color:#fff">
              ₹${flightData.price?.toLocaleString() || '0'}
            </div>
          </div>
          <div style="color:#aaa;margin-bottom:8px">
            <div><strong style="color:#fff">${flightData.airline}</strong> | ${flightData.flight_number || flightData.flightNumber || 'Flight'}</div>
            <div>🕐 ${flightData.departure_time || flightData.departureTime} - ${flightData.arrival_time || flightData.arrivalTime} | ⏱️ ${flightData.duration}</div>
          </div>
          <a href="${flightData.bookingUrl || `https://atarflights.com/search?from=${flightData.from}&to=${flightData.to}`}" 
             target="_blank" 
             style="display:inline-block;background:#14B8A6;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;margin-top:8px">
            🔗 Book Now
          </a>
        </div>
      `;
      
      // Add to transcript
      setTranscript(prev => [...prev, {
        role: 'assistant',
        content: html,
        timestamp: new Date(),
        final: true,
        isHTML: true
      }]);
      
      // Forward to widget UI
      window.postMessage({
        type: 'vapi-message',
        message: { role: 'assistant', content: html }
      }, '*');
      
      // Also forward to parent App.jsx for main page display
      window.postMessage({
        type: 'flight-card-data',
        flight: flightData
      }, '*');
    };

    // Global function to inject multiple flight cards
    window.injectFlightCards = (flights) => {
      console.log('✈️ Injecting multiple flight cards:', flights.length);
      
      flights.forEach((flight, idx) => {
        setTimeout(() => {
          window.injectFlightCard(flight);
        }, idx * 200); // Stagger the injection for smooth animation
      });
    };

    console.log('✅ Flight card injection functions exposed globally');
    console.log('   - window.injectFlightCard(flightData)');
    console.log('   - window.injectFlightCards([...flights])');

    return () => {
      delete window.injectFlightCard;
      delete window.injectFlightCards;
    };
  }, []);

  const handleButtonClick = () => {
    setIsOpen(!isOpen);
  };

  const handleStartCall = async () => {
    if (!vapiClientRef.current) {
      console.error('❌ Vapi client not initialized');
      return;
    }

    try {
      console.log('📞 Starting call with assistant:', assistantId);
      console.log('🔑 Using public key:', publicKey.substring(0, 20) + '...');
      
      setIsConnecting(true);
      
      // Start call - no additional config needed (invalid params were causing 400 error)
      await vapiClientRef.current.start(assistantId);
      
      setTranscript([]); // Clear previous transcript
      setIsConnecting(false);
      console.log('✅ Call started successfully with custom UI only');
    } catch (error) {
      console.group('❌ Vapi error details (start call)');
      console.log('Status:', error.status || error.statusCode);
      console.log('Type:', error.type);
      console.log('Stage:', error.stage);
      console.log('Message:', error.message);
      console.log('Body:', error.body);
      
      // Extract real server response - try multiple methods
      let serverResponse = null;
      let errorDetails = null;
      
      try {
        // Method 1: error.error is a Response object
        if (error.error && typeof error.error.json === 'function') {
          try {
            errorDetails = await error.error.json();
            serverResponse = JSON.stringify(errorDetails, null, 2);
            console.log('✅ Server Response (from error.error.json):', serverResponse);
            console.log('📊 Parsed error details:', errorDetails);
          } catch (e) {
            console.log('❌ Could not parse error.error as JSON:', e);
          }
        }
        
        // Method 2: error.error has text()
        if (!serverResponse && error.error && typeof error.error.text === 'function') {
          try {
            serverResponse = await error.error.text();
            console.log('✅ Server Response (from error.error.text):', serverResponse);
            try {
              errorDetails = JSON.parse(serverResponse);
              console.log('📊 Parsed error details:', errorDetails);
            } catch (e) {
              console.log('Text response (not JSON):', serverResponse);
            }
          } catch (e) {
            console.log('❌ Could not get error.error.text():', e);
          }
        }
        
        // Method 3: Original method
        if (!serverResponse && error.response?.text) {
          serverResponse = await error.response.text();
          console.log('Server Response (from error.response):', serverResponse);
        } else if (!serverResponse && error.response?.json) {
          serverResponse = JSON.stringify(await error.response.json());
          console.log('Server Response (JSON):', serverResponse);
        }
      } catch (e) {
        console.log('❌ Could not extract response:', e);
      }
      
      console.log('Full error object:', error);
      console.groupEnd();
      
      // Parse server response for better error message
      let errorMessage = 'Failed to start call.\n\n';
      
      if (errorDetails) {
        // Use the parsed error details
        if (errorDetails.error) {
          errorMessage += `Error: ${errorDetails.error}\n`;
        }
        if (errorDetails.message) {
          errorMessage += `Message: ${errorDetails.message}\n`;
        }
        if (errorDetails.detail) {
          errorMessage += `Detail: ${errorDetails.detail}\n`;
        }
        
        // Show specific guidance based on error type
        if (errorDetails.message?.includes('not found') || errorDetails.message?.includes('not published')) {
          errorMessage += '\n⚠️ Your assistant is not published!\n';
          errorMessage += 'Go to Vapi dashboard and click "Publish" button.\n';
        } else if (errorDetails.message?.includes('model')) {
          errorMessage += '\n⚠️ Your assistant needs a model!\n';
          errorMessage += 'Go to Model tab and select gpt-3.5-turbo.\n';
        } else if (errorDetails.message?.includes('voice')) {
          errorMessage += '\n⚠️ Your assistant needs a voice!\n';
          errorMessage += 'Go to Voice tab and select a voice provider.\n';
        }
      } else if (serverResponse) {
        // Fallback to string response
        try {
          const parsed = JSON.parse(serverResponse);
          if (parsed.error) {
            errorMessage += `Error: ${parsed.error}\n`;
          }
          if (parsed.message) {
            errorMessage += `Message: ${parsed.message}\n`;
          }
        } catch (e) {
          errorMessage += `Server said: ${serverResponse}\n`;
        }
      } else if (error.status === 400 || error.statusCode === 400 || error.type === 'start-method-error') {
        errorMessage += 'Invalid assistant configuration.\n\n';
        errorMessage += 'Check:\n';
        errorMessage += '• Assistant is published in Vapi dashboard\n';
        errorMessage += '• Assistant has model configured (e.g. gpt-3.5-turbo)\n';
        errorMessage += '• Assistant has voice configured\n';
        errorMessage += '• Public key matches assistant workspace\n';
      } else if (error.status === 401 || error.statusCode === 401) {
        errorMessage += 'Invalid API key. Check your public key.';
      } else if (error.status === 403 || error.statusCode === 403) {
        errorMessage += 'Access denied. Check your Vapi account permissions.';
      } else if (error.message?.includes('microphone')) {
        errorMessage += 'Microphone permission denied.';
      } else {
        errorMessage += error.message || 'Unknown error occurred.';
      }
      
      alert(errorMessage);
    }
  };

  const handleEndCall = () => {
    console.log('🛑 End Call button clicked');
    console.log('  - vapiClientRef:', !!vapiClientRef.current);
    console.log('  - isConnected:', isConnected);
    
    if (vapiClientRef.current) {
      try {
        console.log('🛑 Calling vapiClient.stop()...');
        const stopResult = vapiClientRef.current.stop();
        console.log('✅ vapiClient.stop() returned:', stopResult);
        console.log('✅ Call end request sent');
        
        // Reset states IMMEDIATELY
        setTimeout(() => {
          console.log('🔄 Resetting call states...');
          setIsConnected(false);
          setIsListening(false);
          setIsAssistantSpeaking(false);
          setIsMuted(false);
          muteStateRef.current = false; // ⭐ NEW: Reset mute state ref
          microphoneStreamRef.current = null; // Clear microphone stream reference
          setCallId(null);
          setTranscript([]);
          setShouldPollFlights(false); // ⭐ Reset flight polling flag
          setShouldPollHotels(false); // ⭐ Reset hotel polling flag
          console.log('✅ All states reset');
        }, 100);
        
      } catch (error) {
        console.error('❌ Error ending call:', error);
        // Force reset states even if stop() fails
        setIsConnected(false);
        setIsListening(false);
        setIsAssistantSpeaking(false);
        setIsMuted(false);
        muteStateRef.current = false; // ⭐ NEW: Reset mute state ref
        microphoneStreamRef.current = null; // Clear microphone stream reference
        setCallId(null);
        setTranscript([]);
        setShouldPollFlights(false); // ⭐ Reset flight polling flag
        setShouldPollHotels(false); // ⭐ Reset hotel polling flag
        console.log('✅ States reset after error');
      }
    } else {
      console.warn('⚠️ Cannot end call: Vapi client not initialized');
    }
  };

  const handleToggleMute = () => {
    console.log('🔇 Mute button clicked');
    console.log('  - vapiClientRef:', !!vapiClientRef.current);
    console.log('  - isConnected:', isConnected);
    console.log('  - React state isMuted:', isMuted);
    console.log('  - Ref state muteStateRef.current:', muteStateRef.current);
    
    if (!isConnected || !vapiClientRef.current) {
      console.warn('⚠️ Cannot toggle mute: Not connected or client not initialized');
      return;
    }
    
    try {
      // Use the ref value as the source of truth
      const currentMutedFromRef = muteStateRef.current;
      const newMutedState = !currentMutedFromRef;
      
      console.log('  - Current muted (from ref):', currentMutedFromRef);
      console.log('  - New muted state will be:', newMutedState);
      
      // Update ref FIRST
      muteStateRef.current = newMutedState;
      console.log('  ✅ Updated muteStateRef to:', newMutedState);
      
      // Method 1: Try Vapi SDK methods
      const vapiClient = vapiClientRef.current;
      let muteSuccess = false;
      
      try {
        // Try setMuted
        if (typeof vapiClient.setMuted === 'function') {
          vapiClient.setMuted(newMutedState);
          console.log('✅ vapiClient.setMuted() called successfully');
          muteSuccess = true;
        }
        // Try mute/unmute methods
        else if (newMutedState && typeof vapiClient.mute === 'function') {
          vapiClient.mute();
          console.log('✅ vapiClient.mute() called successfully');
          muteSuccess = true;
        }
        else if (!newMutedState && typeof vapiClient.unmute === 'function') {
          vapiClient.unmute();
          console.log('✅ vapiClient.unmute() called successfully');
          muteSuccess = true;
        }
        // Try call object
        else if (vapiClient.call && typeof vapiClient.call.setMuted === 'function') {
          vapiClient.call.setMuted(newMutedState);
          console.log('✅ vapiClient.call.setMuted() called successfully');
          muteSuccess = true;
        }
      } catch (vapiError) {
        console.warn('⚠️ Vapi mute API failed:', vapiError.message);
      }
      
      // Method 2: Access browser MediaStream directly to mute microphone track
      if (!muteSuccess) {
        try {
          // First try to use stored stream reference
          if (microphoneStreamRef.current) {
            const audioTracks = microphoneStreamRef.current.getAudioTracks();
            if (audioTracks.length > 0) {
              audioTracks.forEach(track => {
                track.enabled = !newMutedState; // enabled=false means muted
                console.log(`✅ Microphone track ${track.label} ${newMutedState ? 'muted' : 'unmuted'}`);
              });
              muteSuccess = true;
            }
          }
          
          // If no stored stream, try to get current stream
          if (!muteSuccess && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
              .then(stream => {
                // Store the stream for future use
                microphoneStreamRef.current = stream;
                const audioTracks = stream.getAudioTracks();
                if (audioTracks.length > 0) {
                  audioTracks.forEach(track => {
                    track.enabled = !newMutedState; // enabled=false means muted
                    console.log(`✅ Microphone track ${track.label} ${newMutedState ? 'muted' : 'unmuted'}`);
                  });
                  muteSuccess = true;
                } else {
                  console.warn('⚠️ No audio tracks found in stream');
                }
              })
              .catch(err => {
                console.warn('⚠️ Could not access MediaStream:', err.message);
              });
          }
        } catch (streamError) {
          console.warn('⚠️ MediaStream access failed:', streamError.message);
        }
      }
      
      // Method 3: Try to find and mute active audio tracks from any source
      if (!muteSuccess) {
        try {
          // Access all media tracks from the page
          if (window.navigator && window.navigator.mediaDevices) {
            // This is a fallback - try to mute any active audio input
            console.log('⚠️ Trying fallback: muting all audio input tracks');
            // Note: This might not work if Vapi manages its own stream internally
          }
        } catch (e) {
          console.warn('⚠️ Fallback mute method failed:', e.message);
        }
      }
      
      // Update React state to match (this is the important part)
      console.log('🔄 Updating React state with setIsMuted(' + newMutedState + ')...');
      setIsMuted(newMutedState);
      console.log('✅ React state updated');
      
      // Log final state for verification
      console.log('🔍 Final muted state: ref=' + muteStateRef.current + ', react=' + newMutedState);
      console.log('   Button will show as ' + (newMutedState ? 'MUTED' : 'UNMUTED'));
      console.log('   Mute operation success:', muteSuccess ? 'YES' : 'NO (UI-only)');
      
    } catch (error) {
      console.error('❌ Unexpected error in handleToggleMute:', error);
      console.error('    - Error message:', error.message);
      console.error('    - Error type:', error.constructor.name);
    }
  };

  const handleClose = () => {
    if (isConnected) {
      handleEndCall();
    }
    setIsOpen(false);
    setTranscript([]);
  };

  // Always show button, even during loading
  // if (isLoading) {
  //   return (
  //     <button className="voice-button loading">
  //       <div className="spinner"></div>
  //     </button>
  //   );
  // }

  return (
    <>
      {/* Floating Button - Rectangle with Icon and Text - Hide when widget opens */}
      {!isOpen && (
        <button 
          className="voice-button"
          onClick={handleButtonClick}
          title="Talk with AI"
        >
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            d="M12 15C13.66 15 15 13.66 15 12V6C15 4.34 13.66 3 12 3C10.34 3 9 4.34 9 6V12C9 13.66 10.34 15 12 15Z" 
            fill="white"
          />
          <path 
            d="M17 12C17 14.76 14.76 17 12 17C9.24 17 7 14.76 7 12H5C5 15.53 7.61 18.43 11 18.92V22H13V18.92C16.39 18.43 19 15.53 19 12H17Z" 
            fill="white"
          />
        </svg>
          <span>TALK WITH AI</span>
        </button>
      )}

      {/* Vapi Panel */}
      {isOpen && (
        <div className="vapi-panel">
          <div className="vapi-panel-header">
            <div className="header-left">
              <div>
                <h3>TALK WITH AI</h3>
                <p>
                  {!isConnected && isConnecting ? 'Connecting...' :
                   !isConnected ? 'Click start to begin' : 
                   isListening ? 'Listening...' : 
                   isAssistantSpeaking ? 'Assistant Speaking...' :
                   'Ready'}
                </p>
              </div>
            </div>
            <div className="header-actions">
              <button className="refresh-btn" onClick={() => setTranscript([])} title="Clear transcript">
                ↻
              </button>
              <button className="close-btn" onClick={handleClose} title="Close">×</button>
            </div>
          </div>

          <div className="vapi-panel-body">
            {/* Transcript Area */}
            <div className="transcript-area">
              {transcript.length === 0 ? (
                <div className="empty-transcript">
                  <div className="mic-icon-large">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                      <line x1="12" y1="19" x2="12" y2="23"></line>
                      <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                  </div>
                  <p className="instruction-text">{isConnected ? 'Listening... Say something!' : 'Click the start button to begin a conversation'}</p>
                </div>
              ) : (
                <>
                  {(() => {
                    // Group consecutive messages of the same role together
                    const groupedMessages = [];
                    let currentGroup = null;
                    
                    transcript.forEach((msg, idx) => {
                      // If HTML messages or different role, start a new group
                      if (msg.isHTML || !currentGroup || currentGroup.role !== msg.role) {
                        if (currentGroup) {
                          groupedMessages.push(currentGroup);
                        }
                        currentGroup = {
                          role: msg.role,
                          contents: [msg],
                          key: idx
                        };
                      } else {
                        // Same role, add to current group (only if not HTML)
                        currentGroup.contents.push(msg);
                      }
                    });
                    
                    // Don't forget the last group
                    if (currentGroup) {
                      groupedMessages.push(currentGroup);
                    }
                    
                    return groupedMessages.map((group, groupIdx) => {
                      const htmlMessages = group.contents.filter(msg => msg.isHTML);
                      const textMessages = group.contents.filter(msg => !msg.isHTML);
                      
                      return (
                        <div key={group.key || groupIdx} className={`transcript-message ${group.role}`}>
                          <div className="message-role">{group.role === 'user' ? 'You' : 'Assistant'}</div>
                          <div className="message-content">
                            {/* Render HTML messages */}
                            {htmlMessages.map((msg, msgIdx) => (
                              <div key={`html-${msgIdx}`} dangerouslySetInnerHTML={{ __html: msg.content }} />
                            ))}
                            {/* Combine text messages into one */}
                            {textMessages.length > 0 && (
                              <div>{textMessages.map(msg => msg.content).join(' ')}</div>
                            )}
                          </div>
                        </div>
                      );
                    });
                  })()}
                  
                  {/* Invisible element for auto-scroll */}
                  <div ref={transcriptEndRef} />
                </>
              )}
            </div>

            {/* Control Buttons */}
            <div className="control-area">
              {!isConnected ? (
                <button className="start-call-btn" onClick={handleStartCall}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                  </svg>
                  Start
                </button>
              ) : (
                <div className="call-controls">
                  <button 
                    className={`mute-btn ${isMuted ? 'muted' : ''}`}
                    onClick={handleToggleMute}
                    title={isMuted ? 'Unmute' : 'Mute'}
                  >
                    {isMuted ? (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                        <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path>
                        <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                      </svg>
                    ) : (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                      </svg>
                    )}
                  </button>
                  <button className="end-call-btn" onClick={handleEndCall}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <rect width="18" height="18" x="3" y="3" rx="2"/>
                    </svg>
                    <span>End Call</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default VoiceButton;