"""
Vapi Tools - Function Calling for Voice Agent
Defines tools that the voice agent can call during conversations
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class VapiTools:
    """Tools for Vapi voice agent function calling"""
    
    def __init__(self):
        self.backend_url = os.getenv("BOOKING_API_URL", "http://localhost:8080")
        self.flight_api_key = os.getenv("FLIGHT_API_KEY")
        self.hotel_api_key = os.getenv("HOTEL_API_KEY")
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> Dict[str, Any]:
        """
        Search for available flights
        
        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trip (optional)
            passengers: Number of passengers
            cabin_class: Cabin class (economy, business, etc.)
            
        Returns:
            Dictionary with flight search results
        """
        try:
            # Normalize airport codes
            origin = self._normalize_airport_code(origin)
            destination = self._normalize_airport_code(destination)
            
            # Make API call to backend
            response = requests.post(
                f"{self.backend_url}/api/search-flights",
                json={
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "passengers": passengers,
                    "cabin_class": cabin_class
                },
                timeout=30
            )
            response.raise_for_status()
            results = response.json()
            
            # Format results for voice response
            formatted = self._format_flight_results(results, passengers)
            
            return {
                "success": True,
                "data": results,
                "voice_response": formatted
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_response": f"I apologize, I encountered an error searching for flights: {str(e)}. Would you like me to try again or connect you with an agent?"
            }
    
    def search_hotels(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
        rooms: int = 1,
        star_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for available hotels
        
        Args:
            destination: Destination city
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            rooms: Number of rooms
            star_rating: Optional star rating filter
            
        Returns:
            Dictionary with hotel search results
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/search-hotels",
                json={
                    "destination": destination,
                    "check_in": check_in,
                    "check_out": check_out,
                    "guests": guests,
                    "rooms": rooms,
                    "star_rating": star_rating
                },
                timeout=30
            )
            response.raise_for_status()
            results = response.json()
            
            formatted = self._format_hotel_results(results)
            
            return {
                "success": True,
                "data": results,
                "voice_response": formatted
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_response": f"I'm sorry, I couldn't find hotels. Would you like me to connect you with an agent?"
            }
    
    def create_booking(
        self,
        booking_type: str,
        item_id: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        passenger_details: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create a booking
        
        Args:
            booking_type: Type of booking (flight, hotel, package)
            item_id: ID of the selected item
            customer_phone: Customer phone number
            customer_email: Customer email (optional)
            passenger_details: List of passenger details
            
        Returns:
            Booking confirmation details
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/create-booking",
                json={
                    "booking_type": booking_type,
                    "item_id": item_id,
                    "customer_phone": customer_phone,
                    "customer_email": customer_email,
                    "passenger_details": passenger_details or []
                },
                timeout=30
            )
            response.raise_for_status()
            booking = response.json()
            
            formatted = self._format_booking_confirmation(booking)
            
            return {
                "success": True,
                "data": booking,
                "voice_response": formatted
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_response": f"I apologize, there was an error creating your booking. Would you like to try again or speak with an agent?"
            }
    
    def get_booking_status(self, booking_reference: str) -> Dict[str, Any]:
        """
        Get status of an existing booking
        
        Args:
            booking_reference: Booking reference number
            
        Returns:
            Booking status details
        """
        try:
            response = requests.get(
                f"{self.backend_url}/api/booking-status",
                params={"booking_reference": booking_reference},
                timeout=15
            )
            response.raise_for_status()
            booking = response.json()
            
            formatted = self._format_booking_status(booking)
            
            return {
                "success": True,
                "data": booking,
                "voice_response": formatted
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_response": f"I couldn't find a booking with reference {booking_reference}. Please check the reference number and try again."
            }
    
    def transfer_to_agent(self, reason: str, priority: str = "medium") -> Dict[str, Any]:
        """
        Initiate transfer to human agent
        
        Args:
            reason: Reason for transfer
            priority: Priority level (low, medium, high)
            
        Returns:
            Transfer initiation response
        """
        agent_phone = os.getenv("HUMAN_AGENT_PHONE")
        
        return {
            "success": True,
            "action": "transfer",
            "transfer_number": agent_phone,
            "reason": reason,
            "priority": priority,
            "voice_response": f"I understand you need additional assistance. Let me connect you with one of our travel experts right away. Please hold."
        }
    
    def cancel_booking(self, booking_reference: str) -> Dict[str, Any]:
        """
        Cancel an existing booking
        
        Args:
            booking_reference: Booking reference number
            
        Returns:
            Cancellation confirmation
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/cancel-booking",
                json={"booking_reference": booking_reference},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "data": result,
                "voice_response": f"Your booking {booking_reference} has been cancelled. You'll receive a refund confirmation via email within 24 hours."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_response": f"I couldn't cancel the booking. Please contact our support team or let me transfer you to an agent."
            }
    
    # Helper methods
    
    def _normalize_airport_code(self, location: str) -> str:
        """Convert city names to airport codes"""
        city_to_airport = {
            # India
            "bengaluru": "BLR", "bangalore": "BLR",
            "mumbai": "BOM", "bombay": "BOM",
            "delhi": "DEL", "new delhi": "DEL",
            "chennai": "MAA", "madras": "MAA",
            "kolkata": "CCU", "calcutta": "CCU",
            "hyderabad": "HYD",
            "pune": "PNQ",
            "ahmedabad": "AMD",
            # Saudi Arabia
            "riyadh": "RUH",
            "jeddah": "JED",
            "dammam": "DMM",
            "mecca": "JED",  # Closest is Jeddah
            "medina": "MED",
            "abha": "AHB",
            "taif": "TIF",
            "tabuk": "TUU",
            # International
            "dubai": "DXB",
            "abu dhabi": "AUH",
            "doha": "DOH",
            "bahrain": "BAH",
            "kuwait": "KWI",
            "muscat": "MCT",
            "singapore": "SIN",
            "london": "LHR",
            "new york": "JFK",
            "los angeles": "LAX",
            "san francisco": "SFO",
            "paris": "CDG",
            "frankfurt": "FRA"
        }
        
        location_lower = location.lower().strip()
        
        # If already an airport code (3 letters)
        if len(location) == 3 and location.isupper():
            return location
        
        # Try to match city name
        return city_to_airport.get(location_lower, location.upper()[:3])
    
    def _format_flight_results(self, results: Dict, passengers: int) -> str:
        """Format flight results as Markdown cards for chat widget"""
        # Get flights from results
        flights = []
        if results.get("success"):
            flights = results.get("outbound_flights", [])
        elif results.get("flights"):
            flights = results.get("flights", [])
        
        if not flights:
            return "I couldn't find any flights for that route. Would you like to try different dates or destinations?"
        
        # Get search criteria
        search = results.get("search_criteria", {})
        origin = search.get("origin", flights[0].get("origin", ""))
        destination = search.get("destination", flights[0].get("destination", ""))
        date = search.get("departure_date", flights[0].get("departure_date", ""))
        
        # Format date nicely
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %b %d")
        except:
            formatted_date = date
        
        # Build Markdown card response
        response = f"### ✈️ {origin} → {destination} | {formatted_date}\n\n"
        response += f"I found **{len(flights)} flight options** for you:\n\n"
        
        # Show top 3 flights as cards
        for i, flight in enumerate(flights[:3], 1):
            airline = flight.get("airline", "Unknown")
            flight_number = flight.get("flight_number", "")
            departure_time = flight.get("departure_time", "")
            arrival_time = flight.get("arrival_time", "")
            duration = flight.get("duration", "")
            cabin_class = flight.get("cabin_class", "economy").title()
            price = flight.get("price", 0) * passengers
            currency = flight.get("currency", "SAR")
            stops = flight.get("stops", 0)
            
            # Get airport names for map links
            origin_name = self._get_airport_name(origin)
            dest_name = self._get_airport_name(destination)
            map_link = self._get_airport_map_link(origin)
            
            # Format price
            if currency == "INR":
                price_str = f"₹{price:,.0f}"
            elif currency == "SAR":
                price_str = f"SAR {price:,.0f}"
            else:
                price_str = f"{currency} {price:,.0f}"
            
            # Stop info
            stop_text = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
            
            # Build card
            response += f"**{i}. {airline} ({flight_number})**  \n"
            response += f"🕓 {departure_time} → {arrival_time} | ⏱ {duration}  \n"
            response += f"💺 {cabin_class} – {price_str} | ✈️ {stop_text}  \n"
            response += f"[📍 View {origin_name} on Google Maps]({map_link})\n\n"
        
        response += f"---\n\n"
        response += "Which flight would you like to book? Just say the number (1, 2, or 3)."
        
        return response
    
    def _format_hotel_results(self, results: Dict) -> str:
        """Format hotel results as Markdown cards for chat widget"""
        if not results.get("hotels"):
            return "I couldn't find any hotels in that area. Would you like to try a different location or dates?"
        
        hotels = results["hotels"][:3]
        destination = results.get("search_criteria", {}).get("destination", "")
        
        # Build Markdown card response
        response = f"### 🏨 Hotels in {destination}\n\n"
        response += f"I found **{len(hotels)} great hotel options** for you:\n\n"
        
        # Show hotels as Markdown cards
        for i, hotel in enumerate(hotels, 1):
            name = hotel.get("name", "Hotel")
            rating = hotel.get("star_rating", "")
            price = hotel.get("price_per_night", 0)
            amenities = hotel.get("amenities", [])
            description = hotel.get("description", "")
            
            # Format price with currency
            currency = hotel.get("currency", "SAR")
            price_text = f"{currency} {price:,.0f}" if currency == "SAR" else f"${price:,.0f}"
            
            # Build card for this hotel
            response += f"**{i}. {name}**"
            if rating:
                response += f" ⭐ {rating}-star\n"
            else:
                response += "\n"
            
            response += f"💰 Price: {price_text} per night\n"
            
            # Add short description (first sentence only)
            if description:
                first_sentence = description.split('.')[0] + '.'
                if len(first_sentence) > 100:
                    first_sentence = first_sentence[:97] + "..."
                response += f"📝 {first_sentence}\n"
            
            # Add Google Maps link
            hotel_query = f"{name}, {destination}".replace(" ", "+")
            maps_url = f"https://www.google.com/maps/search/?api=1&query={hotel_query}"
            response += f"[📍 View {name} on Google Maps]({maps_url})\n\n"
        
        response += "Which hotel would you like to book?"
        
        return response
    
    def _format_booking_confirmation(self, booking: Dict) -> str:
        """Format booking confirmation for voice"""
        ref = booking.get("booking_reference", "UNKNOWN")
        amount = booking.get("total_amount", 0)
        
        return f"Perfect! Your booking is confirmed with reference number {ref}. Total amount is {self._format_currency(amount)}. I'm sending the details and payment link to your phone via SMS. Is there anything else I can help you with?"
    
    def _format_booking_status(self, booking: Dict) -> str:
        """Format booking status for voice"""
        ref = booking.get("booking_reference")
        status = booking.get("status", "unknown")
        
        status_messages = {
            "confirmed": f"Your booking {ref} is confirmed and all set!",
            "pending": f"Your booking {ref} is pending payment. Shall I send you the payment link?",
            "cancelled": f"Your booking {ref} has been cancelled.",
            "completed": f"Your booking {ref} is completed. Hope you had a great trip!"
        }
        
        return status_messages.get(status, f"Your booking {ref} has status: {status}")
    
    def _format_currency(self, amount: float) -> str:
        """Format currency for voice (Indian Rupees)"""
        return f"₹{amount:,.0f}"
    
    def _get_airport_name(self, code: str) -> str:
        """Get full airport name from code"""
        airport_names = {
            # Saudi Arabia
            "RUH": "King Khalid International Airport",
            "JED": "King Abdulaziz International Airport",
            "DMM": "King Fahd International Airport",
            "MED": "Prince Mohammad Bin Abdulaziz Airport",
            "AHB": "Abha Regional Airport",
            "TIF": "Taif Regional Airport",
            "TUU": "Tabuk Regional Airport",
            # UAE
            "DXB": "Dubai International Airport",
            "AUH": "Abu Dhabi International Airport",
            # Other GCC
            "DOH": "Hamad International Airport",
            "BAH": "Bahrain International Airport",
            "KWI": "Kuwait International Airport",
            "MCT": "Muscat International Airport",
            # India
            "BLR": "Kempegowda International Airport",
            "BOM": "Chhatrapati Shivaji Maharaj International Airport",
            "DEL": "Indira Gandhi International Airport",
            "MAA": "Chennai International Airport",
            "CCU": "Netaji Subhas Chandra Bose International Airport",
            "HYD": "Rajiv Gandhi International Airport",
            # International
            "SIN": "Singapore Changi Airport",
            "LHR": "London Heathrow Airport",
            "JFK": "John F. Kennedy International Airport",
            "CDG": "Charles de Gaulle Airport",
            "FRA": "Frankfurt Airport"
        }
        return airport_names.get(code.upper(), f"{code} Airport")
    
    def _get_airport_map_link(self, code: str) -> str:
        """Generate Google Maps link for airport"""
        airport_name = self._get_airport_name(code)
        # URL encode the airport name
        encoded_name = airport_name.replace(" ", "+")
        return f"https://www.google.com/maps/search/?api=1&query={encoded_name}"
    
    def rich_link_formatter(
        self,
        location_name: str,
        location_type: str = "general",
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate clickable Google Maps rich link for any location
        
        This is a standalone tool that can be called by the AI to generate
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
            >>> tools.rich_link_formatter("Hyatt Regency", "hotel", "Riyadh", "Saudi Arabia")
            {
                "success": True,
                "rich_link": "[🏨 View Hyatt Regency on Google Maps](https://...)",
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
            
            # Choose appropriate emoji based on location type
            emoji_map = {
                "hotel": "🏨",
                "airport": "✈️",
                "restaurant": "🍽️",
                "attraction": "🎯",
                "museum": "🏛️",
                "park": "🌳",
                "shopping": "🛍️",
                "cafe": "☕",
                "landmark": "🗼",
                "general": "📍"
            }
            emoji = emoji_map.get(location_type.lower(), "📍")
            
            # Generate Markdown link
            rich_link = f"[{emoji} View {location_name} on Google Maps]({maps_url})"
            
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
                "rich_link": f"📍 {location_name}",
                "voice_response": f"I found {location_name}, but couldn't generate a map link."
            }


# Webhook handler for Vapi function calls
def handle_vapi_function_call(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle function calls from Vapi
    
    Args:
        function_name: Name of the function to call
        parameters: Function parameters
        
    Returns:
        Function execution result
    """
    tools = VapiTools()
    
    function_map = {
        "search_flights": tools.search_flights,
        "search_hotels": tools.search_hotels,
        "create_booking": tools.create_booking,
        "get_booking_status": tools.get_booking_status,
        "transfer_to_agent": tools.transfer_to_agent,
        "cancel_booking": tools.cancel_booking,
        "rich_link_formatter": tools.rich_link_formatter
    }
    
    if function_name not in function_map:
        return {
            "success": False,
            "error": f"Unknown function: {function_name}",
            "voice_response": "I'm sorry, I don't know how to do that yet. Let me connect you with an agent."
        }
    
    try:
        result = function_map[function_name](**parameters)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "voice_response": "I encountered an error. Would you like me to try again or transfer you to an agent?"
        }


if __name__ == "__main__":
    # Test the tools
    tools = VapiTools()
    
    print("Testing Vapi Tools...\n")
    
    # Test flight search
    print("1. Testing flight search...")
    result = tools.search_flights(
        origin="Bengaluru",
        destination="Dubai",
        departure_date="2025-12-10",
        return_date="2025-12-15",
        passengers=1
    )
    print(f"✅ Flight search: {result['success']}")
    print(f"Voice response: {result['voice_response'][:100]}...\n")
    
    # Test hotel search
    print("2. Testing hotel search...")
    result = tools.search_hotels(
        destination="Dubai",
        check_in="2025-12-10",
        check_out="2025-12-15",
        guests=2
    )
    print(f"✅ Hotel search: {result['success']}")
    print(f"Voice response: {result['voice_response'][:100]}...\n")

