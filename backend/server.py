"""
FastAPI Server - Main API server for the voice bot
Handles webhooks from Vapi and provides REST endpoints for flights, hotels, and bookings
"""

import os
import sys
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.flight_api import FlightAPI
from backend.hotel_api import HotelAPI
from backend.booking_service import BookingService
from backend.smtp_email_service import smtp_email_service
# MCP bridge removed - tools configured directly in Vapi dashboard

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Travel.ai Voice Bot API",
    description="Backend API for Vapi voice bot integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
flight_api = FlightAPI()
hotel_api = HotelAPI()
booking_service = BookingService()


# Helper function to generate structured summary
def generate_structured_summary(transcript: List[Dict], booking_details: Optional[Dict] = None) -> str:
    """
    Generate a structured summary in the format:
    - Main Topic/Purpose of the call
    - Key Points Discussed
    - Actions Taken
    - Next Steps
    
    Uses actual conversation data to generate meaningful summaries.
    """
    if not transcript or len(transcript) == 0:
        logger.warning("⚠️ Empty transcript received, using booking details only")
        # If no transcript but has booking details, create summary from booking
        if booking_details:
            return generate_summary_from_booking(booking_details)
        return "No conversation data available. Please complete a call to generate a summary."
    
    import re
    
    # Extract customer name from conversation
    customer_name = "Traveler"  # Default if not found
    
    # Only look at user messages for name extraction, not assistant messages
    user_messages = [msg.get("message", "") or msg.get("text", "") for msg in transcript if msg.get("role") == "user"]
    user_conversation = " ".join(user_messages)
    
    conversation_text = " ".join([msg.get("message", "") or msg.get("text", "") for msg in transcript if msg.get("role") != "system"])
    
    logger.info(f"📝 Processing transcript with {len(transcript)} messages")
    logger.info(f"📝 Conversation preview: {conversation_text[:200]}...")
    
    # Try to extract name from USER messages only (common patterns)
    name_patterns = [
        r"(?:my name is|I'm|this is|call me)\s+(\w+)",
        r"name\s+is\s+(\w+)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, user_conversation, re.IGNORECASE)
        if match:
            potential_name = match.group(1).capitalize()
            # Avoid common words and assistant name
            if potential_name.lower() not in ['help', 'me', 'booking', 'flight', 'travel', 'alex', 'assistant', 'atar', 'attar']:
                customer_name = potential_name
                logger.info(f"👤 Detected customer name: {customer_name}")
            break
    
    # Analyze conversation to extract travel intent
    travel_keywords = {
        'flight': ['flight', 'fly', 'airplane', 'airline'],
        'destination': ['going to', 'travel to', 'visit', 'destination'],
        'hotel': ['hotel', 'accommodation', 'stay', 'room'],
        'dates': ['when', 'date', 'day', 'month', 'tomorrow', 'next week']
    }
    
    intent = detect_travel_intent(conversation_text, travel_keywords)
    
    # Build main topic based on actual conversation and booking details
    main_topic = ""
    if booking_details:
        # Only use this if we have confirmed booking details
        from_loc = booking_details.get("departure_location", "")
        to_loc = booking_details.get("destination", "")
        trip_type = "round-trip" if booking_details.get("return_date") else "one-way"
        
        if from_loc and to_loc:
            main_topic = f"{customer_name} contacted Attar Travel Agency and successfully booked a {trip_type} flight from {from_loc} to {to_loc}."
        else:
            main_topic = f"{customer_name} contacted Attar Travel Agency and completed a flight booking."
    else:
        # No booking made - this is an inquiry or initial contact
        # Check for trip planning vs simple flight inquiry
        conv_lower = conversation_text.lower()
        
        if any(word in conv_lower for word in ['itinerary', 'trip plan', 'day plan', 'day trip', 'multi-day', 'tour package', 'visit', 'sightseeing']):
            # Trip planning discussion
            if any(word in conv_lower for word in ['saudi', 'riyadh', 'jeddah', 'mecca', 'medina']):
                main_topic = f"{customer_name} contacted Attar Travel Agency to discuss multi-day trip planning and itinerary options for Saudi Arabia."
            else:
                main_topic = f"{customer_name} contacted Attar Travel Agency to discuss trip planning and itinerary options."
        elif 'flight' in intent:
            main_topic = f"{customer_name} contacted Attar Travel Agency to inquire about flight bookings and travel options."
        elif 'hotel' in intent:
            main_topic = f"{customer_name} contacted Attar Travel Agency to discuss accommodation options."
        elif len(conversation_text.split()) < 50:
            # Very short conversation - likely just a greeting
            main_topic = f"Initial contact established with Attar Travel Agency. {customer_name} was greeted and introduced to available travel services."
        else:
            main_topic = f"{customer_name} contacted Attar Travel Agency for travel assistance and information."
    
    # Extract key points from actual conversation
    key_points = extract_key_points_from_conversation(transcript, booking_details)
    
    # Actions taken
    actions_taken = generate_actions_taken(booking_details, customer_name)
    
    # Next steps
    next_steps = f"{customer_name} will receive a detailed email shortly with payment instructions and all booking details. No further assistance was requested at this time."
    
    # Format the structured summary with proper spacing
    structured_summary = f"""◆ Main Topic/Purpose of the call

{main_topic}

◆ Key Points Discussed

{chr(10).join('• ' + point for point in key_points)}

◆ Actions Taken

{actions_taken}

◆ Next Steps

{next_steps}"""
    
    logger.info(f"✅ Generated structured summary for {customer_name}")
    return structured_summary


def detect_travel_intent(conversation: str, keywords: dict) -> list:
    """Detect travel intents from conversation"""
    intents = []
    conv_lower = conversation.lower()
    for intent, words in keywords.items():
        if any(word in conv_lower for word in words):
            intents.append(intent)
    return intents


def extract_key_points_from_conversation(transcript: List[Dict], booking_details: Optional[Dict] = None) -> list:
    """Extract key discussion points from the actual conversation"""
    key_points = []
    
    if booking_details:
        # Extract from booking details
        if booking_details.get("departure_date"):
            key_points.append(f"Selected departure date: {booking_details.get('departure_date')}")
        
        if booking_details.get("return_date"):
            key_points.append(f"Selected return date: {booking_details.get('return_date')}")
            
        service_class = booking_details.get("service_details", "Economy")
        key_points.append(f"Selected {service_class} class")
        
        num_travelers = booking_details.get("num_travelers", 1)
        if num_travelers > 1:
            key_points.append(f"Booking for {num_travelers} passengers")
        
        key_points.append("Provided travel preferences and passenger details")
        key_points.append("Confirmed flight details and pricing")
    else:
        # Extract from conversation messages - more accurate for inquiries
        conversation_text = " ".join([
            (msg.get("message", "") or msg.get("text", "")).lower() 
            for msg in transcript
        ])
        
        # Check what was actually discussed - PRIORITIZE trip planning over generic inquiries
        
        # Check for trip planning / itinerary discussions FIRST
        if any(word in conversation_text for word in ['itinerary', 'trip plan', 'day plan', 'day trip', 'multi-day', 'tour package', 'visit', 'sightseeing']):
            key_points.append("Discussed multi-day trip planning and itinerary options")
            
            # Check for specific destinations
            if any(word in conversation_text for word in ['riyadh', 'jeddah', 'mecca', 'medina', 'dammam', 'edge of the world', 'diriyah', 'abha']):
                key_points.append("Explored specific Saudi Arabia destinations and attractions")
            
            if any(word in conversation_text for word in ['activity', 'activities', 'things to do', 'what to see']):
                key_points.append("Discussed activities and experiences during the trip")
                
            if any(word in conversation_text for word in ['day', 'days', 'night', 'nights']):
                key_points.append("Reviewed trip duration and daily schedule options")
        else:
            # Standard flight/travel inquiry
            if any(word in conversation_text for word in ['flight', 'fly', 'airplane']):
                key_points.append("Inquired about flight options and availability")
            
            if any(word in conversation_text for word in ['destination', 'going to', 'travel to']):
                key_points.append("Discussed potential travel destinations")
                
            if any(word in conversation_text for word in ['date', 'when', 'day', 'time']):
                key_points.append("Asked about travel dates and timing")
            
            if any(word in conversation_text for word in ['price', 'cost', 'fare', 'budget']):
                key_points.append("Inquired about pricing and costs")
                
            if any(word in conversation_text for word in ['economy', 'business', 'first class']):
                key_points.append("Discussed cabin class options")
            
            if any(word in conversation_text for word in ['hotel', 'accommodation', 'stay']):
                key_points.append("Asked about accommodation options")
        
        # If very short conversation (greeting only), be explicit about it
        if len(key_points) == 0 or len(conversation_text.split()) < 50:
            key_points = [
                "Initial greeting and introduction to services",
                "Established contact with travel assistant",
                "Expressed interest in travel planning"
            ]
    
    return key_points[:5]  # Limit to 5 key points


def generate_actions_taken(booking_details: Optional[Dict], customer_name: str) -> str:
    """Generate the actions taken section"""
    if booking_details:
        from_loc = booking_details.get("departure_location", "departure city")
        to_loc = booking_details.get("destination", "destination")
        service_class = booking_details.get("service_details", "Economy")
        booking_id = booking_details.get("booking_id", "BK_" + datetime.now().strftime("%Y%m%d%H%M%S"))
        passengers = booking_details.get("num_travelers", 1)
        
        action = f"A reservation was successfully made for {customer_name}'s flight from {from_loc} to {to_loc} in {service_class} Class"
        if passengers > 1:
            action += f" for {passengers} passengers"
        action += f". The confirmation number #{booking_id} was provided."
        return action
    else:
        return "The conversation was an initial inquiry. Travel information and assistance were provided. No booking was completed during this call."


def generate_summary_from_booking(booking_details: Dict) -> str:
    """Generate summary when only booking details are available (no transcript)"""
    from_loc = booking_details.get("departure_location", "")
    to_loc = booking_details.get("destination", "")
    trip_type = "round-trip" if booking_details.get("return_date") else "one-way"
    
    summary = f"""◆ Main Topic/Purpose of the call

A {trip_type} flight booking from {from_loc} to {to_loc}.

◆ Key Points Discussed

• Selected departure date: {booking_details.get('departure_date', 'TBD')}
• Selected {booking_details.get('service_details', 'Economy')} class
• Confirmed flight details and pricing

◆ Actions Taken

A flight reservation was successfully created with confirmation number #{booking_details.get('booking_id', 'PENDING')}.

◆ Next Steps

Detailed booking confirmation and payment instructions will be sent via email shortly."""
    
    return summary


# Helper function to extract booking details from conversation
def extract_booking_from_transcript(transcript: List[Dict], summary: str) -> Optional[Dict]:
    """
    Extract booking details from the conversation transcript and summary.
    Looks for flight booking information in the assistant's messages.
    """
    if not transcript:
        return None
    
    import re
    from datetime import datetime
    
    booking_info = {
        "airline": None,
        "flight_number": None,
        "departure_location": None,
        "destination": None,
        "departure_time": None,
        "arrival_time": None,
        "departure_date": None,
        "return_date": None,
        "duration": None,
        "price": None,
        "currency": "₹",
        "num_travelers": 1,
        "service_details": "Economy",
        "booking_id": None
    }
    
    # Combine all messages into searchable text
    conversation_text = " ".join([
        msg.get("message", "") for msg in transcript 
        if msg.get("role", "").lower() in ["user", "assistant"]
    ])
    
    # Also get user messages separately for more targeted extraction
    user_messages = " ".join([
        msg.get("message", "") for msg in transcript 
        if msg.get("role", "").lower() == "user"
    ])
    
    # Extract airline name
    airlines_pattern = r"(Air India|IndiGo|SpiceJet|Vistara|Emirates|Qatar Airways|Turkish Airlines|Saudi Airlines|Saudia|Flynas|Etihad|Lufthansa)"
    airline_match = re.search(airlines_pattern, conversation_text, re.IGNORECASE)
    if airline_match:
        booking_info["airline"] = airline_match.group(1)
    
    # Extract flight number (e.g., "AI 101", "SG 234")
    flight_num_pattern = r"\b([A-Z]{2}[\s-]?\d{2,4})\b"
    flight_match = re.search(flight_num_pattern, conversation_text)
    if flight_match:
        booking_info["flight_number"] = flight_match.group(1)
    
    # Extract locations (from/to)
    # Look for patterns like "from Mumbai to Dubai", "Mumbai to Dubai", "Bangalore to Jeddah", "BLR to JED"
    # Try multiple patterns with increasing flexibility
    location_patterns = [
        r"(?:from|leaving|departing from|traveling from|flying from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})\s+(?:to|towards|destination|going to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})",
        r"(?:origin|from|departure)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})[,\s]+(?:destination|to|arrival)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})",
        r"(?:flight|travel|go|trip)\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})\s+(?:to|→)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|[A-Z]{3})",
    ]
    
    # Try to extract from conversation text first
    for pattern in location_patterns:
        location_match = re.search(pattern, conversation_text, re.IGNORECASE)
        if location_match:
            booking_info["departure_location"] = location_match.group(1).strip()
            booking_info["destination"] = location_match.group(2).strip()
            break
    
    # If not found, try user messages specifically
    if not booking_info["departure_location"] or not booking_info["destination"]:
        for pattern in location_patterns:
            location_match = re.search(pattern, user_messages, re.IGNORECASE)
            if location_match:
                booking_info["departure_location"] = location_match.group(1).strip()
                booking_info["destination"] = location_match.group(2).strip()
                break
    
    # Extract dates - handle multiple formats
    # Patterns: "March 15", "15th March", "2025-03-15", "December fifteenth 2025", "15/03/2025"
    date_patterns = [
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)\b",
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)\b",
        r"\b(\d{2}/\d{2}/\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty-first|twenty-second|twenty-third|twenty-fourth|twenty-fifth|twenty-sixth|twenty-seventh|twenty-eighth|twenty-ninth|thirtieth|thirty-first)(?:\s+\d{4})?)\b"
    ]
    
    all_dates = []
    for pattern in date_patterns:
        found_dates = re.findall(pattern, conversation_text, re.IGNORECASE)
        all_dates.extend(found_dates)
    
    if len(all_dates) >= 1:
        booking_info["departure_date"] = all_dates[0]
    if len(all_dates) >= 2:
        booking_info["return_date"] = all_dates[1]
    
    # Extract times (e.g., "8:30 AM", "20:30", "6:55a")
    time_pattern = r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|a|p)?)\b"
    times = re.findall(time_pattern, conversation_text)
    if len(times) >= 1:
        booking_info["departure_time"] = times[0]
    if len(times) >= 2:
        booking_info["arrival_time"] = times[1]
    
    # Extract price (e.g., "₹5000", "$500", "5000 rupees")
    price_pattern = r"(?:₹|Rs\.?|INR|rupees?)\s*(\d+(?:,\d+)?)|(\d+(?:,\d+)?)\s*(?:₹|Rs\.?|INR|rupees?)"
    price_match = re.search(price_pattern, conversation_text, re.IGNORECASE)
    if price_match:
        price_str = price_match.group(1) or price_match.group(2)
        booking_info["price"] = int(price_str.replace(",", ""))
    
    # Extract number of passengers
    passenger_pattern = r"(\d+)\s+(?:passenger|traveler|person|people)"
    passenger_match = re.search(passenger_pattern, conversation_text, re.IGNORECASE)
    if passenger_match:
        booking_info["num_travelers"] = int(passenger_match.group(1))
    
    # Extract class (Economy, Business, First)
    class_pattern = r"\b(Economy|Business|First)\s+(?:Class|class)?"
    class_match = re.search(class_pattern, conversation_text, re.IGNORECASE)
    if class_match:
        booking_info["service_details"] = class_match.group(1).capitalize()
    
    # Extract booking reference from transcript
    booking_ref_pattern = r"\b([A-Z]{2,3}[-_]?\d{6,10})\b"
    booking_ref_match = re.search(booking_ref_pattern, conversation_text)
    if booking_ref_match:
        booking_info["booking_id"] = booking_ref_match.group(1)
    else:
        # Generate a booking ID if none found
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        booking_info["booking_id"] = f"BK_{timestamp}"
    
    # STRICT CHECK: Only return booking details if there's clear evidence of an actual booking
    # Look for booking confirmation keywords
    booking_keywords = [
        'booked', 'reserved', 'confirmed', 'confirmation', 'booking', 
        'reservation made', 'successfully made', 'your booking',
        'booking number', 'confirmation number', 'booking reference',
        'booking id', 'pnr', 'ticket'
    ]
    
    has_booking_confirmation = any(keyword in conversation_text.lower() for keyword in booking_keywords)
    
    # Only proceed if we have clear booking confirmation AND valid route
    if not has_booking_confirmation:
        logger.info("⚠️ No booking confirmation found in conversation - no booking details extracted")
    return None
    
    # Must have both locations to be a valid booking
    if not (booking_info["departure_location"] and booking_info["destination"]):
        logger.info("⚠️ Missing departure or destination - no booking details extracted")
        return None
    
    # Additional check: make sure it's not just a greeting or inquiry
    # Greetings often contain phrases like "planning to travel", "would you like to", "can I help"
    inquiry_phrases = [
        'planning to travel', 'would you like', 'can i help', 
        'may i help', 'how can i help', 'welcome to', 'are you planning'
    ]
    
    # If the ONLY mention of locations is in an inquiry phrase, don't extract
    is_just_inquiry = any(phrase in conversation_text.lower() for phrase in inquiry_phrases)
    if is_just_inquiry and len(conversation_text.split()) < 100:  # Short conversation = likely just greeting
        logger.info("⚠️ Detected inquiry/greeting only - no actual booking made")
        return None
    
    logger.info(f"✈️ Extracted booking: {booking_info['airline']} {booking_info['departure_location']} → {booking_info['destination']}")
    return booking_info


# Request/Response Models

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    cabin_class: str = "economy"


class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    guests: int = 1
    rooms: int = 1
    star_rating: Optional[int] = None


class BookingRequest(BaseModel):
    booking_type: str
    item_id: str
    customer_phone: str
    customer_email: Optional[str] = None
    passenger_details: Optional[List[Dict]] = None


class ConversationTranscriptRequest(BaseModel):
    recipient_email: str
    recipient_name: str
    messages: List[Dict]
    call_duration: Optional[int] = None
    booking_details: Optional[Dict] = None


# Store call summaries in memory (in production, use Redis or database)
call_summaries = {}
latest_call_summary = None  # Store the most recent call summary as fallback

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Travel.ai Voice Bot API",
        "version": "1.0.0",
        "integration": "Vapi-only"
    }


@app.get("/api/call-summary/{call_id}")
async def get_call_summary(call_id: str):
    """Get the call summary for a specific call ID"""
    try:
        if call_id in call_summaries:
            return call_summaries[call_id]
        else:
            raise HTTPException(status_code=404, detail="Call summary not found")
    except Exception as e:
        logger.error(f"Error fetching call summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/call-summary-latest")
async def get_latest_call_summary():
    """Get the most recent call summary (fallback when call ID is not available)"""
    try:
        if latest_call_summary:
            return latest_call_summary
        else:
            raise HTTPException(status_code=404, detail="No call summary available yet")
    except HTTPException:
        # Let HTTPException pass through (404 is expected)
        raise
    except Exception as e:
        logger.error(f"Error fetching latest call summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "vapi": "connected",
            "flight_api": "ready",
            "hotel_api": "ready",
            "booking_service": "ready"
        }
    }


@app.post("/test-booking-email")
async def test_booking_email():
    """Test endpoint to send a sample booking confirmation email"""
    try:
        # Sample booking details matching the screenshot format
        booking_details = {
            "airline": "Turkish Airlines",
            "flight_number": "TK 123",
            "departure_location": "JFK",
            "destination": "DPS",
            "departure_time": "6:55a",
            "arrival_time": "7:15p",
            "departure_date": "10/07/2025",
            "return_date": "10/24/2025",
            "duration": "24h 20m",
            "price": 5308,
            "currency": "$",
            "num_travelers": 2,
            "service_details": "Economy",
            "booking_id": "BK_20251007_ABCD1234"
        }
        
        # Sample transcript
        transcript = [
            {"role": "user", "message": "I want to book a flight to Bali"},
            {"role": "assistant", "message": "I'd be happy to help you book a flight to Bali. When would you like to travel?"},
            {"role": "user", "message": "October 7th, returning October 24th"},
            {"role": "assistant", "message": "Perfect! I found a great Turkish Airlines flight for you."}
        ]
        
        # Generate structured summary using the same function as real calls
        structured_summary = generate_structured_summary(transcript, booking_details)
        
        # Send test email
        success = smtp_email_service.send_transcript_with_summary(
            to_email="attartravel25@gmail.com",
            user_name="Valued Customer",
            summary=structured_summary,  # Use structured summary
            transcript=transcript,
            call_duration=180,
            session_id="test-session-12345",
            timestamp="2025-10-22 10:30:00",
            booking_details=booking_details
        )
        
        if success:
            return {
                "success": True,
                "message": "Test booking email sent successfully!",
                "recipient": "attartravel25@gmail.com",
                "booking_details": booking_details
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        logger.error(f"Error sending test booking email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoint for Vapi

@app.post("/webhooks/vapi")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle webhooks from Vapi
    
    Events:
    - call.started: Call initiated
    - call.ended: Call completed
    - message.received: Message received from user
    - speech.start: User started speaking
    - speech.end: User stopped speaking
    """
    try:
        payload = await request.json()
        
        # Vapi sends webhooks in different formats
        # Format 1: {"type": "call.ended", ...}
        # Format 2: {"message": {"type": "end-of-call-report", ...}}
        message = payload.get("message", {})
        event_type = payload.get("type") or payload.get("event") or message.get("type")
        
        logger.info(f"📞 Vapi webhook received: {event_type}")
        logger.info(f"📦 Full payload keys: {list(payload.keys())}")
        
        # Process different Vapi events
        if event_type == "call.started":
            logger.info(f"✅ Call started: {payload.get('callId')}")
            
        elif event_type == "call.ended" or event_type == "end-of-call-report":
            logger.info(f"✅ Call ended: {payload.get('callId')}")
            
            # Extract conversation data - handle both formats
            call_id = payload.get("callId") or payload.get("call_id") or message.get("call", {}).get("id") or message.get("callId") or message.get("id")
            call_data = payload.get("data", {})
            metadata = payload.get("metadata", {})
            
            # For end-of-call-report format
            if event_type == "end-of-call-report":
                message_data = payload.get("message", {})
                analysis = message_data.get("analysis", {})
                artifact = message_data.get("artifact", {})
                call_obj = message_data.get("call", {})
                
                summary = analysis.get("summary", "No summary available")
                transcript = artifact.get("messages", [])
                
                # Try multiple sources for call duration (in seconds)
                call_duration = (
                    message_data.get("duration") or 
                    message_data.get("endedAt") or
                    call_obj.get("duration") or
                    call_obj.get("endedAt")
                )
                
                # Get timestamp - handle Unix timestamp in milliseconds
                timestamp_raw = message_data.get("timestamp") or message_data.get("createdAt") or call_obj.get("createdAt")
                
                logger.info(f"📊 End-of-call report: {len(transcript)} messages")
                logger.info(f"⏱️  Call duration (raw): {call_duration} (type: {type(call_duration).__name__})")
                logger.info(f"📅 Timestamp (raw): {timestamp_raw}")
            else:
                # Original format
                summary = call_data.get("summary", "No summary available")
                transcript = call_data.get("transcript", [])
                
                # Try multiple sources for call duration
                call_duration = call_data.get("duration") or call_data.get("endedAt")
                
                # Get timestamp
                timestamp_raw = call_data.get("timestamp") or call_data.get("createdAt") or payload.get("timestamp")
                
                logger.info(f"📊 Call ended: {len(transcript) if transcript else 0} messages")
                logger.info(f"⏱️  Call duration (raw): {call_duration} (type: {type(call_duration).__name__})")
                logger.info(f"📅 Timestamp (raw): {timestamp_raw}")
            
            # Convert Unix timestamp (milliseconds) to readable date format
            timestamp = None
            if timestamp_raw:
                try:
                    # If it's a large number, it's likely Unix timestamp in milliseconds
                    if isinstance(timestamp_raw, (int, float)) and timestamp_raw > 1000000000000:
                        # Convert milliseconds to seconds
                        timestamp_seconds = timestamp_raw / 1000
                        # Format as readable date
                        from datetime import datetime
                        dt = datetime.fromtimestamp(timestamp_seconds)
                        timestamp = dt.strftime("%B %d, %Y at %I:%M %p")
                    elif isinstance(timestamp_raw, (int, float)):
                        # Already in seconds
                        from datetime import datetime
                        dt = datetime.fromtimestamp(timestamp_raw)
                        timestamp = dt.strftime("%B %d, %Y at %I:%M %p")
                    else:
                        # Already a string, use as is
                        timestamp = str(timestamp_raw)
                    
                    logger.info(f"📅 Timestamp (formatted): {timestamp}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not format timestamp: {e}")
                    timestamp = str(timestamp_raw) if timestamp_raw else None
            
            # Get user email and name
            user_email = metadata.get("user_email") or call_data.get("customer_email")
            user_name = metadata.get("user_name") or call_data.get("customer_name", "Traveler")
            
            # Log extracted metadata
            logger.info(f"📋 Session ID: {call_id}")
            logger.info(f"📅 Timestamp: {timestamp}")
            
            # Extract booking details from transcript or metadata
            booking_details = None
            if metadata.get("booking_details"):
                booking_details = metadata.get("booking_details")
                logger.info(f"✈️ Booking details found in metadata")
            elif call_data.get("booking_details"):
                booking_details = call_data.get("booking_details")
                logger.info(f"✈️ Booking details found in call_data")
            else:
                # Try to extract from transcript messages
                booking_details = extract_booking_from_transcript(transcript, summary)
                if booking_details:
                    logger.info(f"✈️ Booking details extracted from transcript")
            
            # Generate structured summary (Main Topic, Key Points, Actions, Next Steps)
            structured_summary = generate_structured_summary(transcript, booking_details)
            logger.info(f"📋 Generated structured summary")
            
            # Store the summary in memory for retrieval by the widget
            summary_data = {
                "summary": structured_summary,
                "booking_details": booking_details,
                "transcript": transcript,  # Include full transcript
                "timestamp": timestamp,
                "user_name": user_name or "Customer",
                "call_id": call_id
            }
            
            # Store with call ID if available
            if call_id:
                call_summaries[call_id] = summary_data
                logger.info(f"💾 Stored summary for call ID: {call_id}")
            else:
                logger.warning(f"⚠️ No call ID found, using fallback storage")
            
            # Always store as latest (fallback for when call ID is missing)
            global latest_call_summary
            latest_call_summary = summary_data
            logger.info(f"💾 Stored as latest call summary (fallback)")
            
            # Send email in background - always send to Attar Travels
            # If user email not provided, use Attar Travels default email
            if not user_email:
                user_email = "attartravel25@gmail.com"
                user_name = user_name or "Customer"
                logger.info(f"📧 No user email provided, sending to default: {user_email}")
            
            background_tasks.add_task(
                smtp_email_service.send_transcript_with_summary,
                to_email=user_email,
                user_name=user_name,
                summary=structured_summary,  # Use structured summary instead of Vapi's
                transcript=transcript,
                call_duration=call_duration,
                session_id=call_id,
                timestamp=timestamp,
                booking_details=booking_details
            )
            logger.info(f"📧 SMTP Email task queued for {user_email}")
            
            # Return the summary to Vapi so it can be displayed in the widget
            return {
                "received": True,
                "event": event_type,
                "status": "processed",
                "summary": structured_summary,
                "booking_details": booking_details,
                "call_id": call_id
            }
            
        elif event_type == "message.received":
            message = payload.get("message", {})
            logger.info(f"💬 Message: {message}")
            
        elif event_type == "speech.start":
            logger.info(f"🎤 User started speaking")
            
        elif event_type == "speech.end":
            logger.info(f"🎤 User stopped speaking")
        
        # Send acknowledgment
        return {
            "received": True,
            "event": event_type,
            "status": "processed"
        }
        
    except Exception as e:
        logger.error(f"❌ Error handling Vapi webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Flight Endpoints

@app.post("/api/search-flights")
async def search_flights(request: FlightSearchRequest):
    """Search for flights"""
    try:
        logger.info(f"✈️  Flight search: {request.origin} → {request.destination}")
        
        result = flight_api.search_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            passengers=request.passengers,
            cabin_class=request.cabin_class
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching flights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/flight/{flight_id}")
async def get_flight_details(flight_id: str):
    """Get flight details"""
    try:
        details = flight_api.get_flight_details(flight_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=404, detail="Flight not found")


# Hotel Endpoints

@app.post("/api/search-hotels")
async def search_hotels(request: HotelSearchRequest):
    """Search for hotels"""
    try:
        logger.info(f"🏨 Hotel search: {request.destination}")
        
        result = hotel_api.search_hotels(
            destination=request.destination,
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
            rooms=request.rooms,
            star_rating=request.star_rating
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching hotels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hotel/{hotel_id}")
async def get_hotel_details(hotel_id: str):
    """Get hotel details"""
    try:
        details = hotel_api.get_hotel_details(hotel_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=404, detail="Hotel not found")


@app.post("/api/rich-link")
async def generate_rich_link(request: Dict[str, Any]):
    """Generate rich Google Maps link for any location"""
    try:
        from vapi.tools import VapiTools
        tools = VapiTools()
        
        location_name = request.get("location_name")
        location_type = request.get("type", "general")
        city = request.get("city")
        country = request.get("country")
        
        if not location_name:
            raise HTTPException(status_code=400, detail="location_name is required")
        
        result = tools.rich_link_formatter(
            location_name=location_name,
            location_type=location_type,
            city=city,
            country=country
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating rich link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Booking Endpoints

@app.post("/api/create-booking")
async def create_booking(request: BookingRequest):
    """Create a new booking"""
    try:
        logger.info(f"📝 Creating {request.booking_type} booking")
        
        result = booking_service.create_booking(
            booking_type=request.booking_type,
            item_id=request.item_id,
            customer_phone=request.customer_phone,
            customer_email=request.customer_email,
            passenger_details=request.passenger_details
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/booking-status")
async def get_booking_status(booking_reference: str):
    """Get booking status"""
    try:
        result = booking_service.get_booking_status(booking_reference)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cancel-booking")
async def cancel_booking(request: Dict[str, str]):
    """Cancel a booking"""
    try:
        booking_reference = request.get("booking_reference")
        
        if not booking_reference:
            raise HTTPException(status_code=400, detail="booking_reference required")
        
        result = booking_service.cancel_booking(booking_reference)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customer-bookings/{customer_phone}")
async def get_customer_bookings(customer_phone: str):
    """Get all bookings for a customer"""
    try:
        bookings = booking_service.get_customer_bookings(customer_phone)
        return {"bookings": bookings}
    except Exception as e:
        logger.error(f"Error fetching customer bookings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-transcript")
async def send_transcript(request: ConversationTranscriptRequest):
    """Send conversation transcript to user's email"""
    try:
        logger.info(f"📧 Sending transcript to {request.recipient_email}")
        
        success = smtp_email_service.send_transcript_email(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            conversation_messages=request.messages,
            call_duration=request.call_duration,
            booking_details=request.booking_details
        )
        
        if success:
            return {
                "success": True,
                "message": f"Transcript sent successfully to {request.recipient_email}"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send transcript"
            }
        
    except Exception as e:
        logger.error(f"Error sending transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-booking-confirmation")
async def send_booking_confirmation(
    recipient_email: str,
    recipient_name: str,
    booking_reference: str,
    booking_details: Dict,
    transcript: Optional[List[Dict]] = None
):
    """Send booking confirmation with transcript to email"""
    try:
        logger.info(f"📧 Sending booking confirmation to {recipient_email}")
        
        success = smtp_email_service.send_booking_confirmation_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            booking_reference=booking_reference,
            booking_details=booking_details,
            transcript=transcript
        )
        
        if success:
            return {
                "success": True,
                "message": f"Booking confirmation sent to {recipient_email}"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send booking confirmation"
            }
        
    except Exception as e:
        logger.error(f"Error sending booking confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"""
    ╔═══════════════════════════════════════════════════╗
    ║   🎙️  Travel.ai Voice Bot API Server            ║
    ║                                                   ║
    ║   Server running on: http://{host}:{port}       ║
    ║   API docs: http://{host}:{port}/docs           ║
    ║                                                   ║
    ║   Webhooks:                                       ║
    ║   - Vapi: /webhooks/vapi                          ║
    ║   - Yellow.ai: /webhooks/yellow                   ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

