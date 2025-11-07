import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import FlightCard from './components/FlightCard';
import HotelCard from './components/HotelCard';
import VoiceButton from './components/VoiceButton';

const VAPI_PUBLIC_KEY = import.meta.env.VITE_VAPI_PUBLIC_KEY || '577ae6b3-53b9-4a37-b6f6-74e8e8808368';
const VAPI_ASSISTANT_ID = import.meta.env.VITE_VAPI_ASSISTANT_ID || 'e1c04a87-a8cf-4438-a91b-5888f69d1ef2';
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:4000';

// Alex AI Behavior Instructions
const ALEX_INSTRUCTIONS = `You are Alex, the AI travel assistant for Attar Travel Agency.

GREETING (First Message):
"Hello! Welcome to Attar Travel. I'm Alex, your AI travel assistant. I can help you with flight bookings, travel packages, booking management, trip planning, or hotel reservations. What would you like help with today?"

TRIP ITINERARIES - WHEN USER ASKS TO PLAN A TRIP:
When user says "plan trip", "create itinerary", "what to do in Saudi Arabia", present days in this format:

🗓️ **Day 1:** [Activity and details]
🗓️ **Day 2:** [Activity and details]
🗓️ **Day 3:** [Activity and details]

EXAMPLE 3-DAY ITINERARY:
"Perfect! Here's a 3-day itinerary for you:

🗓️ **Day 1:** Arrive in Riyadh → Explore Al Masmak Fort → Visit historical Diriyah

🗓️ **Day 2:** National Museum → Kingdom Centre Tower → Traditional Souqs & Shopping

🗓️ **Day 3:** Edge of the World scenic day trip OR explore local markets & dining

✈️ Flights, accommodation, and budget details available upon request!"

EXAMPLE 5-DAY ITINERARY:
"Here's your 5-day Saudi Arabia adventure:

🗓️ **Day 1:** Arrive Riyadh → Historical sites & orientation tour

🗓️ **Day 2:** Riyadh cultural exploration → Museums & heritage sites

🗓️ **Day 3:** Edge of the World scenic tour OR Flight to Al-Ula

🗓️ **Day 4:** Al-Ula → UNESCO site Hegra & Madain Saleh exploration

🗓️ **Day 5:** Return journey OR additional desert exploration"

KEY RULE: Always present each day on a separate line with 🗓️ **Day [number]:**

10-STEP BOOKING FLOW (Skip steps if info already provided):
Step 1: Origin - Ask departure city
Step 2: Destination - Ask arrival city
Step 3: Airline Preference - Ask preferred airline
Step 4: Departure Time - Ask time preference
Step 5: Departure Date - Ask travel date
Step 6: Trip Type - Ask round trip or one-way
Step 7: Passengers - Ask number of travelers
Step 8: Cabin Class - Ask economy/business/first
Step 9: Seat Preference - Ask window/aisle
Step 10: Meal Preference - Ask vegetarian/non-veg/vegan

SEARCH FLIGHTS:
After collecting details, say: "Great! Searching now..."
Call search_flights function, then say EXACTLY:
"Perfect! I have successfully reserved your search. Here are your flight options:"
Tell user to review cards and select preferred flight.

FINAL CONFIRMATION:
After user selects flight, summarize everything:
"You'll be flying [Flight] from [Origin] to [Destination] on [Date] at [Time].
For [Number] passenger(s) in [Class] with [Seat] and [Meal].
Total: ₹[Amount].
Does everything look good? Say YES to confirm!"

WAIT FOR "YES"

AFTER YES:
Call create_flight_booking with all details.
Say: "Excellent! I've successfully reserved your ticket! Your confirmation number is [ID]. You'll receive an email shortly."

RULES:
✅ Present itineraries with Day 1, Day 2, Day 3 line by line
✅ Say "Here are your flight options:" to show cards
✅ Always positive about bookings
❌ Never say "unable to book" or "booking failed"

Be warm, friendly, and professional!`;

function App() {
  const [flights, setFlights] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [isCallActive, setIsCallActive] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [showFlights, setShowFlights] = useState(false);
  const [showHotels, setShowHotels] = useState(false);
  const [bookingDetails, setBookingDetails] = useState(null);
  const [callSummary, setCallSummary] = useState(null);
  const [showBookingForm, setShowBookingForm] = useState(false);

  // Listen for Vapi widget messages and events
  useEffect(() => {
    // Get reference to the vapi-widget element
    const vapiWidget = document.querySelector('vapi-widget');
    
    const handleMessage = async (event) => {
      if (!event.data) return;

      // Handle Vapi messages
      if (event.data.type === 'vapi-message') {
        const message = event.data.message;
        
        // Add to transcript
        if (message.transcript || message.content) {
          setTranscript(prev => [...prev, {
            role: message.role,
            content: message.transcript || message.content,
            timestamp: new Date()
          }]);
        }

        // Check for flight search trigger
        const text = (message.transcript || message.content || '').toLowerCase();
        if (message.role === 'user' && /flight|show|find|search|travel/i.test(text)) {
          console.log('🔍 Flight query detected:', text);
          await searchFlightsFromTranscript(text);
        }
      }

      // Handle function call results from Vapi
      if (event.data.type === 'function-call-result' || event.data.type === 'function-call') {
        console.log('🔧 Function call event:', event.data);
        const result = event.data.result || event.data.detail || event.data;
        
        // Check for cards in the result
        if (result.cards && result.cards.length > 0) {
          console.log('✈️ Received flight cards from Vapi:', result.cards.length);
          
          // Convert Vapi cards to flight objects
          const flights = result.cards.map(card => {
            // Parse card format: title="BLR → JED", subtitle="Air India | IX 881"
            const [origin, destination] = (card.title || '').split('→').map(s => s.trim());
            const [airline, flightNumber] = (card.subtitle || '').split('|').map(s => s.trim());
            
            // Parse footer: "⏰ 02:15 - 05:30 | 💰 ₹28,450 | ⏱️ 5h 45m"
            const footer = card.footer || '';
            const timeMatch = footer.match(/(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})/);
            const priceMatch = footer.match(/₹([\d,]+)/);
            const durationMatch = footer.match(/⏱️\s*([\dhm\s]+)/);
            
            return {
              id: card.id || `flight-${Date.now()}-${Math.random()}`,
              origin: origin || 'N/A',
              destination: destination || 'N/A',
              airline: airline || 'Airline',
              flight_number: flightNumber || 'N/A',
              departure_time: timeMatch ? timeMatch[1] : '00:00',
              arrival_time: timeMatch ? timeMatch[2] : '00:00',
              price: priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0,
              duration: durationMatch ? durationMatch[1].trim() : 'N/A',
              from: { code: origin, time: timeMatch ? timeMatch[1] : '00:00' },
              to: { code: destination, time: timeMatch ? timeMatch[2] : '00:00' }
            };
          });
          
          console.log('✅ Parsed flights:', flights);
          setFlights(flights);
          setShowFlights(true);
        }
      }

      // Handle booking confirmation
      if (event.data.type === 'booking-confirmed') {
        const booking = event.data.booking;
        setBookingDetails(booking);
        console.log('✅ Booking confirmed:', booking);
        
        // Send booking confirmation email
        await sendBookingConfirmation(booking);
      }

      // Handle call summary
      if (event.data.type === 'call-summary') {
        const summary = event.data.summary;
        setCallSummary(summary);
        console.log('📊 Call summary:', summary);
        
        // Send summary email
        await sendCallSummary(summary);
      }

      // Handle hotel card data from VoiceButton
      if (event.data.type === 'hotel-card-data') {
        const hotelData = event.data.hotel;
        console.log('🏨 Received hotel card data:', hotelData);
        setHotels(prev => [...prev, hotelData]);
        setShowHotels(true);
      }

      // ⭐ CRITICAL: Handle flight card data from VoiceButton
      if (event.data.type === 'flight-card-data') {
        const flightData = event.data.flight;
        console.log('✈️✈️✈️ Received flight card data:', flightData);
        console.log('   Airline:', flightData.airline);
        console.log('   From:', flightData.from || flightData.origin);
        console.log('   To:', flightData.to || flightData.destination);
        console.log('   Price:', flightData.price);
        
        // Add flight to the flights array
        setFlights(prev => {
          // Check if flight already exists (prevent duplicates)
          const exists = prev.some(f => 
            f.id === flightData.id || 
            (f.airline === flightData.airline && 
             f.flight_number === flightData.flight_number &&
             f.departure_time === flightData.departure_time)
          );
          
          if (exists) {
            console.log('⚠️ Flight already exists, skipping duplicate');
            return prev;
          }
          
          console.log(`✅ Adding flight card ${prev.length + 1}`);
          return [...prev, flightData];
        });
        
        // Show flights section
        setShowFlights(true);
        console.log('✅ Flight cards section is now visible');
      }

      // Handle call status
      if (event.data.type === 'call-start') {
        setIsCallActive(true);
        setTranscript([]);
        setFlights([]);
        setHotels([]);
        setShowFlights(false);
        setShowHotels(false);
        setBookingDetails(null);
        setCallSummary(null);
      }
      if (event.data.type === 'call-end') {
        setIsCallActive(false);
        console.log('📞 Call ended - Requesting summary and sending email...');
        // Request call summary from backend (with delay to allow backend processing)
        await requestCallSummary();
        // Call has ended - summary will be displayed automatically
      }
    };

    // Listen for postMessage events from VoiceButton component
    window.addEventListener('message', handleMessage);

    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, []);

  const searchFlightsFromTranscript = async (text) => {
    // Extract origin and destination from text
    const cityMap = {
      'bangalore': 'BLR', 'bengaluru': 'BLR', 'blr': 'BLR',
      'jeddah': 'JED', 'jed': 'JED',
      'dubai': 'DXB', 'dxb': 'DXB',
      'mumbai': 'BOM', 'bom': 'BOM',
      'delhi': 'DEL', 'del': 'DEL'
    };

    let origin = null, destination = null;
    const textLower = text.toLowerCase();

    // Simple extraction (can be improved)
    Object.entries(cityMap).forEach(([city, code]) => {
      if (textLower.includes(city)) {
        if (!origin) origin = code;
        else if (!destination) destination = code;
      }
    });

    if (origin && destination) {
      try {
        const response = await fetch(`${BACKEND_URL}/api/search-flights`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            origin,
            destination,
            departure_date: '2025-12-15',
            passengers: 1,
            cabin_class: 'economy'
          })
        });

        const data = await response.json();
        if (data.flights && data.flights.length > 0) {
          setFlights(data.flights.slice(0, 6));
          setShowFlights(true);
        }
      } catch (error) {
        console.error('❌ Error fetching flights:', error);
      }
    }
  };

  const clearFlights = () => {
    setShowFlights(false);
    setTimeout(() => setFlights([]), 300);
  };

  // Test function to load sample flights
  const loadTestFlights = async () => {
    console.log('🧪 Loading test flights...');
    try {
      const response = await fetch(`${BACKEND_URL}/api/search-flights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: 'BLR',
          destination: 'JED',
          departure_date: '2025-12-15',
          passengers: 1,
          cabin_class: 'economy'
        })
      });

      const data = await response.json();
      console.log('✅ Test flights response:', data);
      
      if (data.flights && data.flights.length > 0) {
        console.log(`📊 Setting ${data.flights.length} flights`);
        setFlights(data.flights.slice(0, 6));
        setShowFlights(true);
      }
    } catch (error) {
      console.error('❌ Error loading test flights:', error);
    }
  };

  // Send booking confirmation email
  const sendBookingConfirmation = async (booking) => {
    try {
      console.log('📧 Sending booking confirmation email...');
      
      const response = await fetch(`${BACKEND_URL}/api/send-booking-confirmation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient_email: booking.customer_email || 'attartravel25@gmail.com',
          recipient_name: booking.customer_name || 'Customer',
          booking_reference: booking.booking_reference || 'BKREF-' + Date.now(),
          booking_details: booking,
          transcript: transcript
        })
      });

      const data = await response.json();
      if (data.success) {
        console.log('✅ Booking confirmation email sent');
        
        // Show success notification
        setTranscript(prev => [...prev, {
          role: 'system',
          content: `✅ Booking confirmed! Confirmation email sent to ${booking.customer_email || 'your email'}.`,
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('❌ Error sending booking confirmation:', error);
    }
  };

  // Send call summary email
  const sendCallSummary = async (summary) => {
    try {
      console.log('📧 Sending call summary email...');
      
      // Format summary as string if it's an object
      let summaryText = summary.summary;
      if (typeof summary.summary === 'object' && summary.summary !== null) {
        // If it's a structured summary object, format it nicely
        if (summary.summary.summary) {
          summaryText = summary.summary.summary;
        } else {
          summaryText = JSON.stringify(summary.summary, null, 2);
        }
      }
      
      const emailData = {
        recipient_email: summary.customer_email || 'attartravel25@gmail.com',
        recipient_name: summary.customer_name || 'Customer',
        transcript: summary.transcript || [],
        summary: summaryText || 'Call completed',
        call_duration: summary.duration || 0,
        session_id: summary.call_id || 'session-' + Date.now(),
        timestamp: summary.timestamp || new Date().toISOString(),
        booking_details: summary.booking_details || bookingDetails
      };
      
      const response = await fetch(`${BACKEND_URL}/api/send-call-summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emailData)
      });

      const data = await response.json();
      if (data.success) {
        console.log('✅ Call summary email sent successfully');
      } else {
        console.warn('⚠️ Email sending returned:', data);
      }
    } catch (error) {
      console.error('❌ Error sending call summary:', error);
    }
  };

  // Request call summary from backend
  const requestCallSummary = async () => {
    try {
      console.log('📊 Requesting call summary from backend...');
      
      // Wait for backend to process the end-of-call-report (Vapi sends this after call ends)
      // Increased delay to ensure backend has processed the webhook
      await new Promise(resolve => setTimeout(resolve, 4000));
      
      // Try fetching summary with retry logic
      let summary = null;
      let attempts = 0;
      const maxAttempts = 3;
      
      while (!summary && attempts < maxAttempts) {
        attempts++;
        console.log(`📊 Attempt ${attempts}/${maxAttempts} to fetch call summary...`);
        
        try {
          const response = await fetch(`${BACKEND_URL}/api/call-summary-latest`);
          
          if (response.ok) {
            const data = await response.json();
            if (data && (data.summary || data.flight_details || data.booking_details)) {
              summary = data;
              console.log('✅ Call summary received:', summary);
              setCallSummary(summary);
              
              // Send summary email automatically (only if backend didn't send it)
              // Backend sends email automatically, but we send as backup
              if (summary.customer_email || summary.transcript) {
                await sendCallSummary(summary);
              }
              break;
            } else {
              console.log('⏳ Summary not ready yet, retrying...');
              await new Promise(resolve => setTimeout(resolve, 2000));
            }
          } else {
            console.log(`⏳ Backend returned ${response.status}, retrying...`);
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        } catch (error) {
          console.error(`❌ Error fetching call summary (attempt ${attempts}):`, error);
          if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        }
      }
      
      if (!summary) {
        console.warn('⚠️ Could not fetch call summary after multiple attempts');
      }
    } catch (error) {
      console.error('❌ Error in requestCallSummary:', error);
    }
  };

  return (
    <div className="app minimal-mode">
      {/* Header - Hidden in minimal mode */}
      <header className="app-header" style={{ display: 'none' }}>
        <div className="header-content">
          <h1>✈️ Attar Travel</h1>
          <p>AI-Powered Flight Search Assistant</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            onClick={loadTestFlights}
            className="test-flights-btn"
          >
            ✈️ Load Sample Flights
          </button>
        {isCallActive && (
          <div className="call-status">
            <div className="pulse"></div>
            <span>Call Active</span>
          </div>
        )}
        </div>
      </header>

      {/* Booking Confirmation Banner */}
      {bookingDetails && (
        <div className="booking-banner">
          <div className="banner-content">
            <span className="banner-icon">✅</span>
            <div className="banner-text">
              <strong>Booking Confirmed!</strong>
              <span>Reference: {bookingDetails.booking_reference || 'PENDING'}</span>
            </div>
            <span className="banner-details">
              {bookingDetails.airline || 'Flight'} • 
              {bookingDetails.departure_location || bookingDetails.from} → 
              {bookingDetails.destination || bookingDetails.to}
            </span>
          </div>
        </div>
      )}

      {/* Call Summary Banner */}
      {callSummary && !isCallActive && (
        <div className="call-summary-section">
          <div className="summary-card">
            <div className="summary-header">
              <span className="summary-icon"></span>
              <h3>Call Summary</h3>
              <button 
                className="close-summary" 
                onClick={() => setCallSummary(null)}
                aria-label="Close summary"
              >
                ✕
              </button>
            </div>
            
            <div className="summary-content">
              {/* Main Summary - Simple text only */}
              {callSummary.summary && (
                <div className="summary-section">
                  <h4>Summary</h4>
                  <div className="summary-text">
                    {(() => {
                      // Handle different summary formats - just display as plain text
                      let summaryDisplay = callSummary.summary;
                      
                      // If it's an object, try to extract the summary text
                      if (typeof callSummary.summary === 'object' && callSummary.summary !== null) {
                        if (callSummary.summary.summary) {
                          summaryDisplay = callSummary.summary.summary;
                        } else {
                          // If it's structured, just get the main topic or convert to string
                          summaryDisplay = callSummary.summary.main_topic || JSON.stringify(callSummary.summary, null, 2);
                        }
                      }
                      
                      return (
                        <p style={{ whiteSpace: 'pre-line', lineHeight: '1.6' }}>
                          {summaryDisplay}
                        </p>
                      );
                    })()}
                  </div>
                </div>
              )}
              
              {/* Call Timestamp */}
              {callSummary.timestamp && (
                <div className="summary-section">
                  <h4>Call Date & Time</h4>
                  <p>{callSummary.timestamp}</p>
                </div>
              )}
              
              {/* Email Status */}
              {callSummary.customer_email && (
                <div className="summary-section email-status">
                  <h4>Email Sent</h4>
                  <p>Call summary and transcript have been sent to: <strong>{callSummary.customer_email || 'attartravel25@gmail.com'}</strong></p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Show when flights OR hotels are available */}
      <main className="app-main" style={{ display: (showFlights && flights.length > 0) || (showHotels && hotels.length > 0) ? 'block' : 'none' }}>
        <div className="content-wrapper-full">
          
          {/* Flight Cards Section - Full Width */}
          {showFlights && flights.length > 0 && (
            <div className={`flights-section-full ${showFlights ? 'visible' : ''}`}>
              <div className="flights-header">
                <h2>✈️ Flight Results</h2>
                {flights.length > 0 && (
                  <span className="flights-count">Found {flights.length} flights</span>
                )}
              </div>
              
              <div className="flights-grid">
                {flights.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">✈️</div>
                    <p>No flights to display</p>
                    <p className="hint">Click the mic button and ask: "Show me flights from Bangalore to Jeddah"</p>
                  </div>
                ) : (
                  flights.map((flight, idx) => (
                    <FlightCard key={idx} flight={flight} />
                  ))
                )}
              </div>
            </div>
          )}

          {/* Hotel Cards Section - Full Width */}
          {showHotels && hotels.length > 0 && (
            <div className={`hotels-section-full ${showHotels ? 'visible' : ''}`}>
              <div className="hotels-header">
                <h2>🏨 Hotel Results</h2>
                {hotels.length > 0 && (
                  <span className="hotels-count">Found {hotels.length} hotels</span>
                )}
              </div>
              
              <div className="hotels-grid">
                {hotels.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">🏨</div>
                    <p>No hotels to display</p>
                    <p className="hint">Click the mic button and ask: "Find hotels in Riyadh"</p>
                  </div>
                ) : (
                  hotels.map((hotel, idx) => (
                    <HotelCard key={idx} hotel={hotel} />
                  ))
                )}
              </div>
            </div>
          )}

        </div>
      </main>

      {/* Voice Assistant Widget - Custom VoiceButton (Working) */}
      <VoiceButton 
        publicKey={VAPI_PUBLIC_KEY}
        assistantId={VAPI_ASSISTANT_ID}
      />
    </div>
  );
}

export default App;

