"""
FastAPI Server - Main API server for the voice bot
Handles webhooks from Vapi and provides REST endpoints for flights, hotels, and bookings
"""

import os
import sys
import json
import time
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.bookings import BookingService
from backend.email_service import smtp_email_service
# from backend.openai_service import openai_service  # Disabled: Using Vapi for AI responses instead
openai_service = None  # Placeholder - not needed for Vapi webhook

# Import Mock Flights Database (Fallback)
try:
    from backend.mock_flights import MockFlightsDatabase
    mock_db_available = True
except ImportError:
    mock_db_available = False
    logger.error("Mock Flights Database not available - REQUIRED!")

# Import Mock Hotels Database
try:
    from backend.mock_hotels import MockHotelsDatabase
    mock_hotels_db_available = True
    logger.info("Mock Hotels Database available")
except ImportError:
    mock_hotels_db_available = False
    logger.error("Mock Hotels Database not available!")

# MCP bridge removed - tools configured directly in Vapi dashboard

# Initialize FastAPI app
app = FastAPI(
    title="Travel.ai Voice Bot API",
    description="Backend API for Vapi voice bot integration",
    version="1.0.0"
)

# In-memory cache for flight cards (call_id -> cards)
flight_cards_cache = {}

# In-memory cache for hotel cards (call_id -> cards)
hotel_cards_cache = {}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services - Use Mock databases only
if mock_db_available:
    logger.info("Using MOCK FLIGHTS DATABASE")
    logger.info("Available routes: BLR->JED, BLR->RUH, BLR->DXB, BLR->CCU, MAA->DXB")
    flight_api = MockFlightsDatabase()
else:
    logger.error("CRITICAL: Mock Flights Database not available!")
    raise ImportError("MockFlightsDatabase must be available")

# Initialize hotels database - Use Mock database only
if mock_hotels_db_available:
    logger.info("Using MOCK HOTELS DATABASE")
    logger.info("Available cities: Riyadh, Jeddah, Al-Ula, Abha, Dammam")
    hotel_api = MockHotelsDatabase()
else:
    logger.error("CRITICAL: Mock Hotels Database not available!")
    raise ImportError("MockHotelsDatabase must be available")

booking_service = BookingService()


# Rich Link Formatter - Generate Google Maps links
def rich_link_formatter(
    location_name: str,
    location_type: str = "general",
    city: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate clickable Google Maps rich link for any location
    
    This is a standalone tool that can be called to generate
    clickable map links for hotels, restaurants, attractions, etc.
    
    Args:
        location_name: Name of the location (e.g., "Hyatt Regency", "Riyadh Airport")
        location_type: Type of location (hotel, airport, restaurant, attraction, museum, park, shopping)
        city: City name (optional, improves accuracy)
        country: Country name (optional, improves accuracy)
        
    Returns:
        Dictionary with:
            - success: Boolean indicating if link was generated
            - rich_link: Markdown formatted clickable link
            - maps_url: Raw Google Maps URL
            - location_name: Original location name
            - type: Location type
            
    Example:
        >>> rich_link_formatter("Hyatt Regency", "hotel", "Riyadh", "Saudi Arabia")
        {
            "success": True,
            "rich_link": "[View Hyatt Regency on Google Maps](https://...)",
            "maps_url": "https://www.google.com/maps/search/?api=1&query=...",
            "location_name": "Hyatt Regency",
            "type": "hotel"
        }
    """
    try:
        # Build search query with context for better accuracy
        query_parts = [location_name]
        
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)
        
        # Create URL-encoded search query
        search_query = ", ".join(query_parts)
        encoded_query = search_query.replace(" ", "+").replace(",", "%2C")
        maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
        
        # Generate Markdown link
        rich_link = f"[View {location_name} on Google Maps]({maps_url})"
        
        # For voice response (don't read the URL aloud)
        voice_response = f"I've added a map link for {location_name}. You can click on it to see the location."
        
        return {
            "success": True,
            "rich_link": rich_link,
            "maps_url": maps_url,
            "location_name": location_name,
            "type": location_type,
            "voice_response": voice_response
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "rich_link": f"{location_name}",
            "voice_response": f"I found {location_name}, but couldn't generate a map link."
        }


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
    try:
        if not transcript or len(transcript) == 0:
            logger.warning(" Empty transcript received, using booking details only")
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
        
        logger.info(f"Processing transcript with {len(transcript)} messages")
        logger.info(f"Conversation preview: {conversation_text[:200]}...")
        
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
                    logger.info(f"Detected customer name: {customer_name}")
                break
        
        # Analyze conversation to extract travel intent
        travel_keywords = {
            'flight': ['flight', 'fly', 'airplane', 'airline'],
            'destination': ['going to', 'travel to', 'visit', 'destination'],
            'hotel': ['hotel', 'accommodation', 'stay', 'room'],
            'dates': ['when', 'date', 'day', 'month', 'tomorrow', 'next week']
        }
        
        intent = detect_travel_intent(conversation_text, travel_keywords)
        
        # Extract key information from conversation for professional summary
        # Only include what was actually discussed - no generic content
        # IMPORTANT: Only extract from USER messages to avoid assistant's generic responses
        summary_parts = []
        
        # Extract important details from USER messages only
        conv_lower = conversation_text.lower()
        user_messages_text = " ".join(user_messages).lower()
        
        # Check if user actually asked for flights (not just assistant mentioned it)
        user_asked_flights = any(word in user_messages_text for word in ['flight', 'fly', 'airplane', 'airline', 'book flight', 'search flight', 'find flight'])
        
        # Extract flight information ONLY if user asked for flights
        if user_asked_flights:
            # Try to extract origin and destination
            origin_patterns = [
                r'(?:from|leaving|departing)\s+([a-z\s]+?)(?:\s+to|\s+on|\s+for|$)',
                r'flight\s+from\s+([a-z\s]+?)(?:\s+to|\s+on|$)',
            ]
            dest_patterns = [
                r'(?:to|going to|traveling to|destination)\s+([a-z\s]+?)(?:\s+on|\s+for|\s+date|$)',
                r'flight.*?to\s+([a-z\s]+?)(?:\s+on|\s+for|$)',
            ]
            
            origin = None
            destination = None
            
            for pattern in origin_patterns:
                match = re.search(pattern, user_messages_text, re.IGNORECASE)
                if match:
                    origin = match.group(1).strip()
                    # Clean up common words
                    origin = re.sub(r'\b(from|leaving|departing)\b', '', origin, flags=re.IGNORECASE).strip()
                    if origin and len(origin.split()) <= 3:
                        break
            
            for pattern in dest_patterns:
                match = re.search(pattern, user_messages_text, re.IGNORECASE)
                if match:
                    destination = match.group(1).strip()
                    # Clean up common words
                    destination = re.sub(r'\b(to|going|traveling|destination)\b', '', destination, flags=re.IGNORECASE).strip()
                    if destination and len(destination.split()) <= 3:
                        break
            
            # Extract date
            date_patterns = [
                r'(?:on|for|date)\s+([a-z]+\s+\d{1,2},?\s+\d{4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(november|december|january|february|march|april|may|june|july|august|september|october)\s+(\d{1,2})',
            ]
            travel_date = None
            for pattern in date_patterns:
                match = re.search(pattern, user_messages_text, re.IGNORECASE)
                if match:
                    travel_date = match.group(0).strip()
                    break
            
            # Build flight discussion summary
            if origin and destination:
                flight_desc = f"Flight inquiry from {origin.title()} to {destination.title()}"
                if travel_date:
                    flight_desc += f" on {travel_date}"
                summary_parts.append(flight_desc)
            else:
                summary_parts.append("Flight booking inquiry")
        
        # Extract hotel information ONLY if user asked for hotels
        user_asked_hotels = any(word in user_messages_text for word in ['hotel', 'accommodation', 'stay', 'room', 'book hotel', 'search hotel', 'find hotel'])
        
        if user_asked_hotels:
            hotel_city = None
            city_patterns = [
                r'hotel\s+(?:in|at|for)\s+([a-z\s]+?)(?:\s+for|\s+on|$)',
                r'(?:stay|accommodation)\s+(?:in|at)\s+([a-z\s]+?)(?:\s+for|$)',
            ]
            for pattern in city_patterns:
                match = re.search(pattern, user_messages_text, re.IGNORECASE)
                if match:
                    hotel_city = match.group(1).strip()
                    if hotel_city and len(hotel_city.split()) <= 2:
                        break
            
            if hotel_city:
                summary_parts.append(f"Hotel accommodation inquiry for {hotel_city.title()}")
            else:
                summary_parts.append("Hotel accommodation inquiry")
        
        # Don't add trip planning unless explicitly discussed in detail
        # Only add if user specifically asked about itinerary/trip planning (not just mentioned)
        
        # Add booking details if booking was made
        if booking_details:
            from_loc = booking_details.get("departure_location", "")
            to_loc = booking_details.get("destination", "")
            trip_type = "round-trip" if booking_details.get("return_date") else "one-way"
            departure_date = booking_details.get("departure_date", "")
            airline = booking_details.get("airline", "")
            flight_number = booking_details.get("flight_number", "")
            booking_id = booking_details.get("booking_id", "")
            
            booking_info = []
            if from_loc and to_loc:
                booking_info.append(f"{trip_type.title()} flight from {from_loc} to {to_loc}")
            if departure_date:
                booking_info.append(f"departure date: {departure_date}")
            if airline:
                booking_info.append(f"airline: {airline}")
            if flight_number:
                booking_info.append(f"flight number: {flight_number}")
            if booking_id:
                booking_info.append(f"booking confirmation: {booking_id}")
            
            if booking_info:
                summary_parts.append(f"Booking completed - {', '.join(booking_info)}")
        
        # Only create summary if we have actual content to summarize
        # Don't add generic fallback messages
        if not summary_parts:
            # Only add minimal summary if conversation was very short
            if len(conversation_text.split()) < 30:
                discussion_summary = "Brief initial contact."
            else:
                # Try to extract at least flight or hotel info from USER messages
                if user_asked_flights:
                    discussion_summary = "Flight inquiry discussed."
                elif user_asked_hotels:
                    discussion_summary = "Hotel inquiry discussed."
                else:
                    discussion_summary = "Travel inquiry discussed."
        else:
            # Create professional summary from actual content
            discussion_summary = ". ".join(summary_parts) + "."
        
        logger.info(f"Generated professional summary: {discussion_summary}")
        return discussion_summary
    except Exception as e:
        logger.error(f"Error generating structured summary: {e}", exc_info=True)
        # Return fallback summary
        if booking_details:
            try:
                return generate_summary_from_booking(booking_details)
            except Exception as fallback_error:
                logger.error(f"Error in fallback summary generation: {fallback_error}", exc_info=True)
        return "Travel inquiry and assistance discussion."


def detect_travel_intent(conversation: str, keywords: dict) -> list:
    """Detect travel intents from conversation"""
    try:
        intents = []
        if not conversation:
            logger.warning(" Empty conversation string provided to detect_travel_intent")
            return intents
        
        conv_lower = conversation.lower()
        for intent, words in keywords.items():
            if any(word in conv_lower for word in words):
                intents.append(intent)
        return intents
    except Exception as e:
        logger.error(f"Error detecting travel intent: {e}", exc_info=True)
        return []


def extract_key_points_from_conversation(transcript: List[Dict], booking_details: Optional[Dict] = None) -> list:
    """Extract key discussion points from the actual conversation"""
    try:
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
    except Exception as e:
        logger.error(f"Error extracting key points from conversation: {e}", exc_info=True)
        return ["Travel inquiry and assistance discussion"]


def generate_actions_taken(booking_details: Optional[Dict], customer_name: str) -> str:
    """Generate the actions taken section"""
    try:
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
    except Exception as e:
        logger.error(f"Error generating actions taken: {e}", exc_info=True)
        return "Travel information and assistance were provided during the conversation."


def generate_summary_from_booking(booking_details: Dict) -> str:
    """Generate summary when only booking details are available (no transcript)"""
    try:
        if not booking_details:
            logger.warning(" Empty booking_details provided to generate_summary_from_booking")
            return "Flight booking discussion."
        
        from_loc = booking_details.get("departure_location", "")
        to_loc = booking_details.get("destination", "")
        trip_type = "round-trip" if booking_details.get("return_date") else "one-way"
        departure_date = booking_details.get("departure_date", "")
        airline = booking_details.get("airline", "")
        flight_number = booking_details.get("flight_number", "")
        booking_id = booking_details.get("booking_id", "")
        
        summary_parts = []
        if from_loc and to_loc:
            summary_parts.append(f"Flight inquiry from {from_loc} to {to_loc}")
        if departure_date:
            summary_parts.append(f"departure date: {departure_date}")
        
        # Add booking details
        booking_info = []
        if airline:
            booking_info.append(f"airline: {airline}")
        if flight_number:
            booking_info.append(f"flight number: {flight_number}")
        if booking_id:
            booking_info.append(f"booking confirmation: {booking_id}")
        
        if booking_info:
            summary_parts.append(f"Booking completed - {', '.join(booking_info)}")
        
        summary = ". ".join(summary_parts) + "." if summary_parts else "Flight booking discussion."
        
        return summary
    except Exception as e:
        logger.error(f"Error generating summary from booking: {e}", exc_info=True)
        return "Flight booking discussion."


# Helper function to extract booking details from conversation
def extract_booking_from_transcript(transcript: List[Dict], summary: str) -> Optional[Dict]:
    """
    Extract booking details from the conversation transcript and summary.
    Looks for flight booking information in the assistant's messages.
    """
    try:
        if not transcript:
            logger.warning(" Empty transcript provided to extract_booking_from_transcript")
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
            logger.info(" No booking confirmation found in conversation - no booking details extracted")
            return None
        
        # Must have both locations to be a valid booking
        if not (booking_info["departure_location"] and booking_info["destination"]):
            logger.info(" Missing departure or destination - no booking details extracted")
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
            logger.info(" Detected inquiry/greeting only - no actual booking made")
            return None
        
        logger.info(f"Extracted booking: {booking_info['airline']} {booking_info['departure_location']} -> {booking_info['destination']}")
        return booking_info
    except Exception as e:
        logger.error(f"Error extracting booking from transcript: {e}", exc_info=True)
        return None


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


class CallSummaryEmailRequest(BaseModel):
    recipient_email: str
    recipient_name: str
    transcript: Optional[List[Dict]] = None
    summary: Optional[str] = None
    call_duration: Optional[int] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None
    booking_details: Optional[Dict] = None


# Store call summaries in memory (in production, use Redis or database)
call_summaries = {}
latest_call_summary = None  # Store the most recent call summary as fallback

# Helper function for email sending with error handling
def _send_email_with_error_handling(
    user_email: str,
    user_name: str,
    summary: str,
    transcript: List[Dict],
    call_duration: Optional[int],
    call_id: Optional[str],
    timestamp: Optional[str],
    booking_details: Optional[Dict],
    booking_confirmed: bool
):
    """Helper function to send email with proper error logging"""
    try:
        logger.info(f"Attempting to send email to {user_email}")
        success = smtp_email_service.send_transcript_with_summary(
            to_email=user_email,
            user_name=user_name,
            summary=summary,
            transcript=transcript,
            call_duration=call_duration,
            session_id=call_id,
            timestamp=timestamp,
            booking_details=booking_details,
            is_booking_confirmation=booking_confirmed
        )
        if success:
            logger.info(f"Email sent successfully to {user_email}")
        else:
            logger.error(f"Failed to send email to {user_email} - check SMTP configuration")
    except Exception as e:
        logger.error(f"Exception in email sending task: {e}", exc_info=True)
        logger.error(f"Email: {user_email}, Name: {user_name}")

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    try:
        return {
            "status": "running",
            "service": "Travel.ai Voice Bot API",
            "version": "1.0.0",
            "integration": "Vapi-only"
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}", exc_info=True)
        return {
            "status": "error",
            "service": "Travel.ai Voice Bot API",
            "error": str(e)
        }


@app.get("/api/call-summary/{call_id}")
async def get_call_summary(call_id: str):
    """Get the call summary for a specific call ID"""
    try:
        if call_id in call_summaries:
            return call_summaries[call_id]
        else:
            raise HTTPException(status_code=404, detail="Call summary not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call summary: {e}", exc_info=True)
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
        logger.error(f"Error fetching latest call summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        return {
            "status": "healthy",
            "services": {
                "vapi": "connected",
                "flight_api": "ready",
                "hotel_api": "ready",
                "booking_service": "ready"
            }
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
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
        logger.error(f"Error sending test booking email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoint for Vapi

@app.post("/webhook")
async def vapi_function_webhook(request: Request):
    """
    Direct webhook for Vapi function calls (search_flights)
    Vapi calls this endpoint directly when search_flights function is triggered
    Returns flight cards in Vapi's expected format
    """
    try:
        payload = await request.json()
        logger.info(f"📩 Received Vapi function call: {json.dumps(payload, indent=2)}")
        
        # Extract parameters - Vapi sends in "parameters" key or at top level
        params = payload.get("parameters", {}) or payload
        
        origin = params.get('origin', '').strip()
        destination = params.get('destination', '').strip()
        departure_date = params.get('departure_date', '2025-12-20').strip()
        
        # Fallback: Check nested 'arguments' if still empty
        if not origin and payload.get('arguments'):
            args = payload.get('arguments', {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except:
                    args = {}
            origin = args.get('origin', '').strip()
            destination = args.get('destination', '').strip()
            departure_date = args.get('departure_date', '2025-12-20').strip()
        
        logger.info(f"Function call - Origin: {origin}, Destination: {destination}, Date: {departure_date}")
        logger.info(f"Payload keys: {list(payload.keys())}")
        
        if not origin or not destination:
            logger.warning("Missing origin or destination")
            logger.warning(f"Full payload for debugging: {json.dumps(payload, indent=2)}")
            return JSONResponse(content={
                "error": "missing_parameters",
                "required": ["origin", "destination"]
            })
        
        # Search flights using flight API
        flight_results = flight_api.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=None,
            passengers=1,
            cabin_class='economy'
        )
        
        if flight_results.get("success") and flight_results.get("outbound_flights"):
            flights = flight_results.get("outbound_flights", [])
            logger.info(f"Found {len(flights)} flights")
            
            # Format flights as Vapi cards
            cards = []
            for flight in flights[:6]:  # Limit to 6 cards
                card = {
                    "title": f"{flight.get('origin')} → {flight.get('destination')}",
                    "subtitle": f"{flight.get('airline')} | {flight.get('flight_number')}",
                    "body": f"{flight.get('departure_time')} - {flight.get('arrival_time')} | {flight.get('duration')}",
                    "footer": f"₹{flight.get('price'):,} | Economy",
                    "buttons": [
                        {
                            "text": "Book Now",
                            "url": f"https://booking.example.com/flight/{flight.get('id', 'default')}"
                        }
                    ]
                }
                cards.append(card)
            
            # Vapi expects this format: { "cards": [...], "text": "..." }
            vapi_response = {
                "cards": cards,
                "text": ""  # Empty - AI will generate response from system prompt
            }
            
            #  Store cards in cache for frontend polling
            call_id = payload.get("call", {}).get("id") or payload.get("callId") or "latest"
            flight_cards_cache[call_id] = {
                "cards": cards,
                "text": "",  # Empty - AI handles responses
                "timestamp": time.time(),
                "origin": origin,
                "destination": destination
            }
            logger.info(f"Cached {len(cards)} cards for call_id: {call_id}")
            
            logger.info(f"Returning {len(cards)} flight cards to Vapi")
            return JSONResponse(content=vapi_response)
        else:
            logger.warning(" No flights found")
            return JSONResponse(content={
                "error": "no_flights_found",
                "origin": origin,
                "destination": destination,
                "date": departure_date
            })
            
    except Exception as e:
        logger.error(f"Error in Vapi function webhook: {e}", exc_info=True)
        return JSONResponse(content={
            "error": "search_failed",
            "message": str(e)
        }, status_code=500)


@app.get("/api/flight-cards/{call_id}")
async def get_flight_cards(call_id: str):
    """
    Get cached flight cards for a specific call
    Frontend polls this endpoint to retrieve cards
    """
    try:
        logger.info(f"Frontend polling for cards with call_id: {call_id}")
        
        # If 'latest' is requested, return the most recent cache entry
        if call_id == 'latest' and flight_cards_cache:
            # Get the most recent entry (highest timestamp)
            latest_entry = max(flight_cards_cache.items(), key=lambda x: x[1]["timestamp"])
            latest_call_id, cache_data = latest_entry
            age = time.time() - cache_data["timestamp"]
            logger.info(f"Returning latest cached cards (call_id: {latest_call_id}, age: {age:.1f}s): {len(cache_data['cards'])} cards")
            
            return JSONResponse(content={
                "success": True,
                "cards": cache_data["cards"],
                "text": cache_data["text"],
                "cached_at": cache_data["timestamp"],
                "age_seconds": age,
                "actual_call_id": latest_call_id
            })
        elif call_id in flight_cards_cache:
            cache_data = flight_cards_cache[call_id]
            age = time.time() - cache_data["timestamp"]
            logger.info(f"Found cached cards (age: {age:.1f}s): {len(cache_data['cards'])} cards")
            
            return JSONResponse(content={
                "success": True,
                "cards": cache_data["cards"],
                "text": cache_data["text"],
                "cached_at": cache_data["timestamp"],
                "age_seconds": age
            })
        else:
            logger.info(f"No cached cards found for call_id: {call_id}")
            logger.info(f"Available call_ids in cache: {list(flight_cards_cache.keys())}")
            
            return JSONResponse(content={
                "success": False,
                "cards": [],
                "message": "No cards found for this call_id. Cards may not have been generated yet."
            })
            
    except Exception as e:
        logger.error(f"Error fetching flight cards: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "cards": [],
            "error": str(e)
        }, status_code=500)


@app.post("/api/clear-cache")
async def clear_cache():
    """
    Clear all cached cards (flight and hotel)
    Called by frontend when a new call starts to ensure fresh state
    """
    try:
        logger.info("")
        logger.info("" * 30)
        logger.info("FRONTEND REQUESTED CACHE CLEAR")
        logger.info("" * 30)
        
        flight_count = len(flight_cards_cache)
        hotel_count = len(hotel_cards_cache)
        
        flight_cards_cache.clear()
        hotel_cards_cache.clear()
        
        logger.info(f"Cleared {flight_count} flight cache entries")
        logger.info(f"Cleared {hotel_count} hotel cache entries")
        logger.info("All caches cleared - ready for fresh search")
        logger.info("")
        
        return JSONResponse(content={
            "success": True,
            "message": "All caches cleared",
            "cleared": {
                "flights": flight_count,
                "hotels": hotel_count
            }
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/hotel-cards/{call_id}")
async def get_hotel_cards(call_id: str):
    """
    Get cached hotel cards for a specific call
    Frontend polls this endpoint to retrieve hotel cards
    """
    try:
        logger.info(f"Frontend polling for hotel cards with call_id: {call_id}")
        
        # If 'latest' is requested, return the most recent cache entry
        if call_id == 'latest' and hotel_cards_cache:
            # Get the most recent entry (highest timestamp)
            latest_entry = max(hotel_cards_cache.items(), key=lambda x: x[1]["timestamp"])
            latest_call_id, cache_data = latest_entry
            age = time.time() - cache_data["timestamp"]
            logger.info(f"Returning latest cached hotel cards (call_id: {latest_call_id}, age: {age:.1f}s): {len(cache_data['cards'])} cards")
            
            return JSONResponse(content={
                "success": True,
                "cards": cache_data["cards"],
                "text": cache_data["text"],
                "cached_at": cache_data["timestamp"],
                "age_seconds": age,
                "actual_call_id": latest_call_id
            })
        elif call_id in hotel_cards_cache:
            cache_data = hotel_cards_cache[call_id]
            age = time.time() - cache_data["timestamp"]
            logger.info(f"Found cached hotel cards (age: {age:.1f}s): {len(cache_data['cards'])} cards")
            
            return JSONResponse(content={
                "success": True,
                "cards": cache_data["cards"],
                "text": cache_data["text"],
                "cached_at": cache_data["timestamp"],
                "age_seconds": age
            })
        else:
            logger.info(f"No cached hotel cards found for call_id: {call_id}")
            logger.info(f"Available call_ids in hotel cache: {list(hotel_cards_cache.keys())}")
            
            return JSONResponse(content={
                "success": False,
                "cards": [],
                "message": "No hotel cards found for this call_id. Cards may not have been generated yet."
            })
            
    except Exception as e:
        logger.error(f"Error fetching hotel cards: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "cards": [],
            "error": str(e)
        }, status_code=500)


@app.post("/tool-calls")
async def tool_calls_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Vapi tool-calls webhook endpoint (alias for /webhooks/vapi)
    This endpoint forwards all requests to the main vapi_webhook handler
    """
    logger.info("Received request at /tool-calls - forwarding to vapi_webhook")
    return await vapi_webhook(request, background_tasks)


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
        
        logger.info(f"Vapi webhook received: {event_type}")
        logger.info(f"Full payload keys: {list(payload.keys())}")
        logger.info(f"Full payload: {json.dumps(payload, indent=2)[:500]}")  # Log first 500 chars
        
        # Handle function calls from Vapi (tool-calls is the actual event type)
        # Also check if payload has function/parameters even without event type
        has_function_call = (
            event_type in ["function-call", "tool-call", "tool-calls"] or
            "functionCall" in payload or
            "toolCall" in payload or
            "parameters" in payload or
            (message and "toolCall" in message)
        )
        
        if has_function_call:
            logger.info("Function call received from Vapi")
            logger.info(f"Event type: {event_type}")
            
            # Extract function details with proper precedence
            function_call = (
                payload.get("functionCall") 
                or payload.get("toolCall") 
                or message.get("toolCall")
                or (message.get("toolCalls", [{}])[0] if message.get("toolCalls") else {})
            )
            
            #  CRITICAL: Extract toolCallId for response
            tool_call_id = (
                function_call.get("id")
                or payload.get("toolCallId")
                or payload.get("id")
                or "unknown"
            )
            logger.info(f"🔑 Tool Call ID: {tool_call_id}")
            
            # Extract function name from multiple possible locations
            function_name = (
                function_call.get("name") 
                or function_call.get("function", {}).get("name") 
                or payload.get("function") 
                or payload.get("tool")
            )
            
            # Extract parameters and handle both string and dict formats
            parameters = (
                function_call.get("parameters") 
                or function_call.get("arguments") 
                or function_call.get("function", {}).get("arguments") 
                or payload.get("parameters", {})
            )
            
            # If parameters is a string (JSON), parse it
            if isinstance(parameters, str):
                try:
                    parameters = json.loads(parameters)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse parameters as JSON: {parameters}")
                    parameters = {}
            
            logger.info(f"Function: {function_name}")
            logger.info(f"Parameters: {parameters}")
            logger.info(f"Full function_call: {json.dumps(function_call, indent=2) if function_call else 'Empty'}")
            
            # Handle search_flights function
            if function_name == "search_flights":
                try:
                    # Extract parameters
                    origin = parameters.get("origin", "").strip()
                    destination = parameters.get("destination", "").strip()
                    departure_date = parameters.get("departure_date", "").strip()
                    return_date = parameters.get("return_date")
                    passengers = parameters.get("passengers", 1)
                    cabin_class = parameters.get("cabin_class", "economy")
                    
                    logger.info(f"VAPI Function Call: search_flights")
                    logger.info(f"   Raw Origin: {origin}")
                    logger.info(f"   Raw Destination: {destination}")
                    logger.info(f"   Raw Departure Date: {departure_date}")
                    
                    #  FIX: Extract just the city name if VAPI sends "Bengaluru BLR" or "Bangalore BLR"
                    # Split by space and take the first part (city name)
                    if origin and ' ' in origin:
                        origin = origin.split()[0]  # Get "Bengaluru" from "Bengaluru BLR"
                    if destination and ' ' in destination:
                        destination = destination.split()[0]  # Get "Jeddah" from "Jeddah JED"
                    
                    logger.info(f"   Cleaned Origin: {origin}")
                    logger.info(f"   Cleaned Destination: {destination}")
                    
                    # Normalize city names to airport codes if needed
                    city_mappings = {
                        "bangalore": "Bangalore",
                        "bengaluru": "Bangalore",
                        "blr": "Bangalore",
                        "jeddah": "Jeddah",
                        "jed": "Jeddah",
                        "riyadh": "Riyadh",
                        "ruh": "Riyadh",
                        "dubai": "Dubai",
                        "dxb": "Dubai"
                    }
                    
                    origin = city_mappings.get(origin.lower(), origin)
                    destination = city_mappings.get(destination.lower(), destination)
                    
                    logger.info(f"Normalized - Origin: {origin}, Destination: {destination}")
                    
                    # Convert date format from YYYYMMDD to YYYY-MM-DD if needed
                    if departure_date and len(departure_date) == 8 and departure_date.isdigit():
                        # Convert 20251228 to 2025-12-28
                        departure_date = f"{departure_date[0:4]}-{departure_date[4:6]}-{departure_date[6:8]}"
                        logger.info(f"Converted date to: {departure_date}")
                    
                    # Handle natural language dates (e.g., "January 15", "jan 15")
                    if departure_date and not departure_date[0:4].isdigit():
                        logger.info(f"Processing natural language date: {departure_date}")
                        
                        # Month mapping
                        month_map = {
                            'january': '01', 'jan': '01',
                            'february': '02', 'feb': '02',
                            'march': '03', 'mar': '03',
                            'april': '04', 'apr': '04',
                            'may': '05',
                            'june': '06', 'jun': '06',
                            'july': '07', 'jul': '07',
                            'august': '08', 'aug': '08',
                            'september': '09', 'sep': '09',
                            'october': '10', 'oct': '10',
                            'november': '11', 'nov': '11',
                            'december': '12', 'dec': '12'
                        }
                        
                        import re
                        from datetime import datetime
                        
                        # Try to extract month and day from natural language
                        date_lower = departure_date.lower()
                        day_match = re.search(r'\b(\d{1,2})\b', date_lower)
                        month_match = None
                        
                        for month_name, month_num in month_map.items():
                            if month_name in date_lower:
                                month_match = month_num
                                break
                        
                        if day_match and month_match:
                            day = day_match.group(1).zfill(2)
                            #  FIX: For January/Feb dates, use 2025. For other months, use 2026
                            month_num = int(month_match)
                            if month_num <= 2:  # January or February
                                year = 2025
                            else:
                                year = 2026  # Use 2026 for months after February
                            departure_date = f"{year}-{month_match}-{day}"
                            logger.info(f" Converted natural date to: {departure_date}")
                        else:
                            logger.warning(f" Could not parse natural language date: {departure_date}")
                            # Use default date
                            departure_date = "2025-12-20"
                            logger.info(f" Using default date: {departure_date}")
                    
                    if not origin or not destination:
                        logger.error(" Origin or destination is empty")
                        return JSONResponse(content={
                            "results": [{
                                "toolCallId": tool_call_id,
                                "result": ""  # Empty - AI will ask for missing parameters from system prompt
                            }]
                        })
                    
                    # Ensure departure_date is set
                    if not departure_date:
                        departure_date = "2025-12-20"
                    
                    logger.info(f"Searching flights: {origin} -> {destination} on {departure_date}")
                    
                    # Search flights using flight API
                    flight_results = flight_api.search_flights(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date or "2025-12-20",
                        return_date=return_date,
                        passengers=passengers,
                        cabin_class=cabin_class
                    )
                    
                    if flight_results.get("success"):
                        flights = flight_results.get("outbound_flights", [])
                        logger.info(f"Found {len(flights)} flights")
                        
                        #  CRITICAL: Return in VAPI's CARD FORMAT for native rendering in chat
                        # Format flights as VAPI cards
                        cards = []
                        for flight in flights[:6]:  # Limit to 6 cards
                            card = {
                                "title": f"{flight.get('origin')} → {flight.get('destination')}",
                                "subtitle": f"{flight.get('airline')} | {flight.get('flight_number')}",
                                "footer": f" {flight.get('departure_time')} - {flight.get('arrival_time')} |  ₹{flight.get('price'):,} |  {flight.get('duration')}",
                                "buttons": [
                                    {
                                        "text": "Book Now ",
                                        "url": f"https://booking.example.com/flight/{flight.get('id', 'default')}"
                                    }
                                ]
                            }
                            cards.append(card)
                        
                        # Vapi expects "cards" at top level with "text" for the message
                        # Format: { "cards": [...], "text": "message" }
                        vapi_response = {
                            "cards": cards,
                            "text": ""  # Empty - AI will generate response from system prompt
                        }
                        
                        logger.info(f"Returning to VAPI: {len(cards)} flight cards with text message")
                        logger.info(f"First card: {json.dumps(cards[0], indent=2) if cards else 'No cards'}")
                        logger.info(f"Full VAPI response: {json.dumps(vapi_response, indent=2)}")
                        
                        #  Store cards in cache for frontend polling
                        call_id = payload.get("call", {}).get("id") or message.get("call", {}).get("id") or payload.get("callId") or "latest"
                        flight_cards_cache[call_id] = {
                            "cards": cards,
                            "text": vapi_response["text"],
                            "timestamp": time.time(),
                            "origin": origin,
                            "destination": destination
                        }
                        logger.info(f"Cached {len(cards)} cards for call_id: {call_id}")
                        
                        #  Return proper Vapi format with toolCallId and results
                        # Vapi expects result to be a STRING, not an object
                        return JSONResponse(
                            content={
                                "results": [{
                                    "toolCallId": tool_call_id,
                                    "result": "",  # Empty string - AI will generate response from system prompt when cards are present
                                    "cards": cards  #  CRITICAL: Include cards so frontend gets them!
                                }]
                            },
                            status_code=200,
                            media_type="application/json"
                        )
                    else:
                        logger.warning(" No flights found")
                        return JSONResponse(
                            content={
                                "results": [{
                                    "toolCallId": tool_call_id,
                                    "result": ""  # Empty - AI will handle "no flights found" response from system prompt
                                }]
                            },
                            status_code=200,
                            media_type="application/json"
                        )
                        
                except Exception as e:
                    logger.error(f"Error in search_flights function: {e}", exc_info=True)
                    return JSONResponse(
                        content={
                            "results": [{
                                "toolCallId": tool_call_id,
                                "result": ""  # Empty - AI will handle error response from system prompt
                            }]
                        },
                        status_code=200,
                        media_type="application/json"
                    )
            
            # Handle search_hotels function
            elif function_name == "search_hotels":
                try:
                    logger.info("")
                    logger.info("" * 35)
                    logger.info("SEARCH HOTELS FUNCTION CALLED")
                    logger.info("" * 35)
                    logger.info(f"Tool Call ID: {tool_call_id}")
                    
                    # Extract parameters
                    city = parameters.get("city", "").strip()
                    logger.info(f"City Parameter: {city}")
                    
                    if not city:
                        logger.error("City parameter is empty")
                        return JSONResponse(
                            content={
                                "results": [{
                                    "toolCallId": tool_call_id,
                                    "result": ""  # Empty - AI will ask for city from system prompt
                                }]
                            }
                        )
                    
                    # Search hotels using hotel API
                    logger.info(f"Searching hotels in: {city}")
                    hotel_results = hotel_api.search_hotels(city)
                    
                    if not hotel_results.get("success"):
                        logger.warning(f"No hotels found for: {city}")
                        return JSONResponse(
                            content={
                                "results": [{
                                    "toolCallId": tool_call_id,
                                    "result": ""  # Empty - AI will handle "no hotels found" response from system prompt
                                }]
                            }
                        )
                    
                    hotels = hotel_results.get("hotels", [])
                    logger.info(f"Found {len(hotels)} hotels in {city}")
                    
                    # Format hotels as Vapi cards
                    cards = []
                    for hotel in hotels[:6]:  # Limit to 6 cards
                        stars_display = "*" * hotel.get("stars", 0)
                        card = {
                            "title": f"{hotel.get('name')}",
                            "subtitle": f"{stars_display} {hotel.get('type')} | {hotel.get('location')}",
                            "footer": f"{hotel.get('price')} | {hotel.get('reviews', 'No reviews')[:50]}...",
                            "buttons": [
                                {
                                    "text": "View on Google Maps",
                                    "url": hotel.get('google_maps_url', '#')
                                }
                            ]
                        }
                        cards.append(card)
                    
                    # Vapi expects "cards" at top level with "text" for the message
                    vapi_response = {
                        "cards": cards,
                        "text": ""  # Empty - AI will generate response from system prompt
                    }
                    
                    logger.info(f"Returning to VAPI: {len(cards)} hotel cards with text message")
                    logger.info(f"First card: {json.dumps(cards[0], indent=2) if cards else 'No cards'}")
                    
                    #  Store cards in cache for frontend polling
                    call_id = payload.get("call", {}).get("id") or message.get("call", {}).get("id") or payload.get("callId") or "latest"
                    hotel_cards_cache[call_id] = {
                        "cards": cards,
                        "text": vapi_response["text"],
                        "timestamp": time.time(),
                        "city": city
                    }
                    logger.info(f"Cached {len(cards)} hotel cards for call_id: {call_id}")
                    
                    #  Return proper Vapi format with toolCallId and results
                    return JSONResponse(
                        content={
                            "results": [{
                                "toolCallId": tool_call_id,
                                "result": "",  # Empty string - AI will generate response from system prompt when cards are present
                                "cards": cards  #  CRITICAL: Include cards so frontend gets them!
                            }]
                        },
                        status_code=200,
                        media_type="application/json"
                    )
                        
                except Exception as e:
                    logger.error(f"Error in search_hotels function: {e}", exc_info=True)
                    return JSONResponse(
                        content={
                            "results": [{
                                "toolCallId": tool_call_id,
                                "result": ""  # Empty - AI will handle error response from system prompt
                            }]
                        },
                        status_code=200,
                        media_type="application/json"
                    )
            
            else:
                logger.warning(f"Unknown function: {function_name}")
                return JSONResponse(
                    content={
                        "results": [{
                            "toolCallId": tool_call_id,
                            "result": ""  # Empty - AI will handle unknown function from system prompt
                        }]
                    },
                    status_code=200,
                    media_type="application/json"
                )
        
        # Process different Vapi events
        elif event_type == "call.started":
            call_id = payload.get('callId') or payload.get('call_id') or message.get('call', {}).get('id')
            logger.info(f"Call started: {call_id}")
            
            #  CRITICAL: Clear flight AND hotel cards cache for this call to ensure fresh start
            logger.info(" Clearing flight and hotel cards cache for new call")
            flight_cards_cache.clear()
            hotel_cards_cache.clear()
            logger.info(" Both caches cleared - widget will start empty")
            
        elif event_type == "call.ended" or event_type == "end-of-call-report":
            logger.info(f"Call ended: {payload.get('callId')}")
            
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
                logger.info(f" Call duration (raw): {call_duration} (type: {type(call_duration).__name__})")
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
                logger.info(f" Call duration (raw): {call_duration} (type: {type(call_duration).__name__})")
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
                    logger.warning(f"Could not format timestamp: {e}")
                    timestamp = str(timestamp_raw) if timestamp_raw else None
            
            # Get user email and name
            user_email = metadata.get("user_email") or call_data.get("customer_email")
            user_name = metadata.get("user_name") or call_data.get("customer_name", "Traveler")
            
            # Log extracted metadata
            logger.info(f" Session ID: {call_id}")
            logger.info(f"📅 Timestamp: {timestamp}")
            
            # Extract booking details from transcript or metadata
            booking_details = None
            if metadata.get("booking_details"):
                booking_details = metadata.get("booking_details")
                logger.info(f" Booking details found in metadata")
            elif call_data.get("booking_details"):
                booking_details = call_data.get("booking_details")
                logger.info(f" Booking details found in call_data")
            else:
                # Try to extract from transcript messages
                booking_details = extract_booking_from_transcript(transcript, summary)
                if booking_details:
                    logger.info(f" Booking details extracted from transcript")
            
            # Generate structured summary (Main Topic, Key Points, Actions, Next Steps)
            structured_summary = generate_structured_summary(transcript, booking_details)
            logger.info(f" Generated structured summary")
            
            # Store the summary in memory for retrieval by the widget
            # Format flight_details for frontend display
            flight_details = None
            booking_confirmed = False
            booking_id = None
            
            if booking_details:
                flight_details = {
                    "origin": booking_details.get("departure_location", "N/A"),
                    "destination": booking_details.get("destination", "N/A"),
                    "date": booking_details.get("departure_date", "N/A"),
                    "passengers": booking_details.get("num_travelers", 1)
                }
                booking_confirmed = booking_details.get("status") == "confirmed" or booking_details.get("booking_id") is not None
                booking_id = booking_details.get("booking_id")
            
            summary_data = {
                "summary": structured_summary,
                "flight_details": flight_details,  # Formatted for frontend
                "booking_confirmed": booking_confirmed,
                "booking_id": booking_id,
                "booking_details": booking_details,  # Keep full details for email
                "transcript": transcript,  # Include full transcript
                "timestamp": timestamp,
                "customer_name": user_name or "Customer",
                "customer_email": user_email,
                "duration": call_duration,
                "call_id": call_id
            }
            
            # Store with call ID if available
            if call_id:
                call_summaries[call_id] = summary_data
                logger.info(f" Stored summary for call ID: {call_id}")
            else:
                logger.warning(f" No call ID found, using fallback storage")
            
            # Always store as latest (fallback for when call ID is missing)
            global latest_call_summary
            latest_call_summary = summary_data
            logger.info(f" Stored as latest call summary (fallback)")
            
            # Send email in background - check if booking is confirmed
            booking_confirmed = booking_details and (
                booking_details.get("status") == "confirmed" or 
                booking_details.get("booking_id") is not None
            )
            
            background_tasks.add_task(
                _send_email_with_error_handling,
                user_email,
                user_name,
                structured_summary,
                transcript,
                call_duration,
                call_id,
                timestamp,
                booking_details,
                booking_confirmed
            )
            
            if booking_confirmed:
                logger.info(f" Booking confirmation email queued for {user_email}")
            else:
                logger.info(f" Conversation summary email queued for {user_email}")
            
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
            logger.info(f" Message: {message}")
            
        elif event_type == "speech.start":
            logger.info(f"🎤 User started speaking")
            
        elif event_type == "speech.end":
            logger.info(f"🎤 User stopped speaking")
        
        # Send acknowledgment - ensure proper JSONResponse for all cases
        logger.info(f" Webhook processed successfully: {event_type}")
        return JSONResponse(
            content={
                "received": True,
                "event": event_type,
                "status": "processed"
            },
            status_code=200,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f" Error handling Vapi webhook: {e}")
        logger.error(f" Traceback:", exc_info=True)
        return JSONResponse(
            content={
                "received": False,
                "error": str(e),
                "status": "error"
            },
            status_code=500,
            media_type="application/json"
        )


# OpenAI + Flight Integration Endpoint

@app.post("/api/process-query")
async def process_query_with_openai(request: Dict[str, Any]):
    """
    Process user query with OpenAI to extract intent and search flights
    Returns structured flight cards for the widget
    """
    try:
        user_message = request.get("message", "")
        
        # Ensure message is a string
        if not isinstance(user_message, str):
            user_message = str(user_message)
        
        user_message = user_message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="message is required")
        
        logger.info(f"🤖 Processing user query with OpenAI: {user_message}")
        
        # Step 1: Extract flight parameters using OpenAI
        extraction_result = openai_service.extract_flight_query(user_message)
        
        if not extraction_result["success"]:
            return {
                "success": False,
                "error": "extraction_failed",
                "flights": []
            }
        
        extracted_data = extraction_result["data"]
        intent = extracted_data.get("intent")
        
        logger.info(f"🎯 Detected intent: {intent}")
        logger.info(f"📊 Extracted data: {extracted_data}")
        
        # Step 2: Handle different intents
        if intent == "search_flights":
            # Check if we have required data
            if not extracted_data.get("origin") or not extracted_data.get("destination"):
                return {
                    "success": False,
                    "error": "missing_parameters",
                    "required": ["origin", "destination"],
                    "flights": [],
                    "extracted_data": extracted_data
                }
            
            if not extracted_data.get("departure_date"):
                return {
                    "success": False,
                    "error": "missing_parameters",
                    "required": ["departure_date"],
                    "flights": [],
                    "extracted_data": extracted_data
                }
            
            # Search flights using the flight API
            flight_search_result = flight_api.search_flights(
                origin=extracted_data["origin"],
                destination=extracted_data["destination"],
                departure_date=extracted_data["departure_date"],
                return_date=extracted_data.get("return_date"),
                passengers=extracted_data.get("passengers", 1),
                cabin_class=extracted_data.get("cabin_class", "economy")
            )
            
            if not flight_search_result["success"]:
                return {
                    "success": False,
                    "error": "no_flights_found",
                    "flights": []
                }
            
            # Step 3: Format flights for display
            outbound_flights = flight_search_result["outbound_flights"]
            formatted_flights = openai_service.format_flights_for_display(outbound_flights)
            
            logger.info(f" Found {len(formatted_flights)} flights")
            
            return {
                "success": True,
                "flights": formatted_flights,
                "search_criteria": flight_search_result["search_criteria"],
                "intent": intent
            }
        
        elif intent == "flight_status":
            return {
                "success": True,
                "error": "not_implemented",
                "flights": [],
                "intent": intent
            }
        
        else:  # general_inquiry
            return {
                "success": True,
                "flights": [],
                "intent": intent
            }
        
    except Exception as e:
        logger.error(f" Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Flight Endpoints

@app.post("/api/search-flights")
async def search_flights_direct(request: Dict[str, Any]):
    """
    Direct flight search endpoint for frontend
    Calls mock flights database directly - no OpenAI extraction needed
    """
    try:
        origin = request.get("origin")
        destination = request.get("destination")
        departure_date = request.get("departure_date", "2025-12-20")
        
        logger.info(f" Direct flight search: {origin} → {destination} on {departure_date}")
        
        if not origin or not destination:
            return {
                "success": False,
                "message": "Origin and destination are required",
                "flights": []
            }
        
        # Call mock database directly
        flight_results = flight_api.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            passengers=request.get("passengers", 1),
            cabin_class=request.get("cabin_class", "economy")
        )
        
        logger.info(f" Direct search returned: {len(flight_results.get('outbound_flights', []))} flights")
        
        return {
            "success": flight_results.get("success", False),
            "message": flight_results.get("message", ""),
            "flights": flight_results.get("outbound_flights", []),
            "total": len(flight_results.get("outbound_flights", []))
        }
        
    except Exception as e:
        logger.error(f" Error in direct flight search: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "flights": []
        }


@app.post("/api/vapi-search-flights")
async def vapi_search_flights(request: Dict[str, Any]):
    """
    VAPI-specific flight search endpoint
    Returns simple text response that VAPI can speak
    
    Args:
        request: Dictionary containing origin, destination, departure_date, etc.
        
    Returns:
        Dictionary with result text for VAPI to speak
    """
    try:
        # Extract parameters (VAPI sends them in different formats)
        origin = request.get("origin")
        destination = request.get("destination")
        departure_date = request.get("departure_date")
        
        logger.info(f"VAPI flight search: {origin} → {destination} on {departure_date}")
        
        if not origin or not destination or not departure_date:
            return {"error": "missing_parameters", "required": ["origin", "destination", "departure_date"]}
        
        # Use the configured flight_api (Mock DB by default)
        flight_search_result = flight_api.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            passengers=request.get("passengers", 1),
            cabin_class=request.get("cabin_class", "economy")
        )
        
        if not flight_search_result.get("success"):
            return {
                "error": "no_flights_found",
                "origin": origin,
                "destination": destination,
                "date": departure_date
            }
        
        outbound_flights = flight_search_result.get("outbound_flights", [])
        
        if len(outbound_flights) == 0:
            return {
                "error": "no_flights_found",
                "origin": origin,
                "destination": destination,
                "date": departure_date
            }
        
        # Return flight data only - AI will generate response from system prompt
        logger.info(f" Found {len(outbound_flights)} flights")
        
        return {
            "success": True,
            "flights": outbound_flights,
            "count": len(outbound_flights)
        }
        
    except Exception as e:
        logger.error(f" Error in VAPI flight search: {e}")
        return {"error": "search_failed", "message": str(e)}


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
        logger.info(f" Hotel search: {request.destination}")
        
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
        logger.error(f" Error searching hotels: {e}", exc_info=True)
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
        location_name = request.get("location_name")
        location_type = request.get("type", "general")
        city = request.get("city")
        country = request.get("country")
        
        if not location_name:
            raise HTTPException(status_code=400, detail="location_name is required")
        
        #  Use local rich_link_formatter function (no longer using vapi.tools)
        result = rich_link_formatter(
            location_name=location_name,
            location_type=location_type,
            city=city,
            country=country
        )
        
        return result
        
    except Exception as e:
        logger.error(f" Error generating rich link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Booking Endpoints

@app.post("/api/create-booking")
async def create_booking(request: BookingRequest):
    """Create a new booking"""
    try:
        logger.info(f" Creating {request.booking_type} booking")
        
        result = booking_service.create_booking(
            booking_type=request.booking_type,
            item_id=request.item_id,
            customer_phone=request.customer_phone,
            customer_email=request.customer_email,
            passenger_details=request.passenger_details
        )
        
        return result
        
    except Exception as e:
        logger.error(f" Error creating booking: {e}", exc_info=True)
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
        logger.error(f" Error getting booking status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customer-bookings/{customer_phone}")
async def get_customer_bookings(customer_phone: str):
    """Get all bookings for a customer"""
    try:
        bookings = booking_service.get_customer_bookings(customer_phone)
        return {"bookings": bookings}
    except Exception as e:
        logger.error(f" Error fetching customer bookings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-transcript")
async def send_transcript(request: ConversationTranscriptRequest):
    """Send conversation transcript to user's email"""
    try:
        logger.info(f" Sending transcript to {request.recipient_email}")
        
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
        logger.error(f" Error sending transcript: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-call-summary")
async def send_call_summary_email(request: CallSummaryEmailRequest):
    """Send call summary email (used by frontend after call ends)"""
    try:
        logger.info(f" Sending call summary email to {request.recipient_email}")
        
        # Convert transcript list to messages format if needed
        messages = request.transcript if request.transcript else []
        
        # Check if booking is confirmed
        booking_confirmed = request.booking_details and (
            request.booking_details.get("status") == "confirmed" or 
            request.booking_details.get("booking_id") is not None
        )
        
        # Use send_transcript_with_summary for better formatting
        success = smtp_email_service.send_transcript_with_summary(
            to_email=request.recipient_email,
            user_name=request.recipient_name,
            summary=request.summary or "Call completed",
            transcript=messages,
            call_duration=request.call_duration,
            session_id=request.session_id,
            timestamp=request.timestamp,
            booking_details=request.booking_details,
            is_booking_confirmation=booking_confirmed
        )
        
        if success:
            logger.info(f" Call summary email sent successfully to {request.recipient_email}")
            return {
                "success": True,
                "message": f"Call summary sent successfully to {request.recipient_email}"
            }
        else:
            logger.warning(f" Failed to send call summary email")
            return {
                "success": False,
                "message": "Failed to send call summary"
            }
        
    except Exception as e:
        logger.error(f" Error sending call summary email: {e}", exc_info=True)
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
        logger.info(f" Sending booking confirmation to {recipient_email}")
        
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
        logger.error(f" Error sending booking confirmation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-flights")
async def search_flights(request: Request):
    """
    Universal flight search endpoint for Vapi voice assistant
    Uses mock database for flight data
    
    Request body:
    {
        "origin": "BLR",
        "destination": "JED",
        "departure_date": "2025-12-20",
        "passengers": 1,
        "cabin_class": "economy"
    }
    """
    try:
        data = await request.json()
        
        origin = data.get("origin", "").upper()
        destination = data.get("destination", "").upper()
        departure_date = data.get("departure_date", "2025-12-20")
        passengers = data.get("passengers", 1)
        cabin_class = data.get("cabin_class", "economy")
        
        logger.info(f" Universal search: {origin} → {destination} on {departure_date}")
        
        if not origin or not destination:
            return JSONResponse({
                "success": False,
                "message": "Origin and destination are required",
                "flights": []
            })
        
        # Use mock database
        if mock_db_available:
            logger.info(f" Using mock database for {origin}→{destination}")
            
            flight_results = flight_api.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                passengers=passengers,
                cabin_class=cabin_class
            )
            
            if flight_results.get("success"):
                flights = flight_results.get("outbound_flights", [])
                return JSONResponse({
                    "success": True,
                    "source": "mock_database",
                    "message": f"Found {len(flights)} flights (demo data)",
                    "flights": flights,
                    "total": len(flights)
                })
        
        # No flights found
        return JSONResponse({
            "success": False,
            "source": "none",
            "message": f"No flights found from {origin} to {destination}",
            "flights": [],
            "total": 0
        }, status_code=404)
        
    except Exception as e:
        logger.error(f" Error in universal search: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error: {str(e)}",
            "flights": []
        }, status_code=500)



if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 4000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"""
    ╔═══════════════════════════════════════════════════╗
    ║     Travel.ai Voice Bot API Server            ║
    ║                                                   ║
    ║   Server running on: http://{host}:{port}       ║
    ║   API docs: http://{host}:{port}/docs           ║
    ║                                                   ║
    ║   Webhooks:                                       ║
    ║   - Vapi: /webhooks/vapi                          ║
    ║                                                   ║
    ║   Flight API: Bright Data Real-Time              ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

