"""
Hotel API - Hotel Search and Booking Backend
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class HotelAPI:
    """Hotel search and booking API - No API keys required!"""
    
    def __init__(self):
        # No API keys needed - uses mock data and free Google Maps links
        pass
    
    def search_hotels(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
        rooms: int = 1,
        star_rating: Optional[int] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search for hotels
        
        Args:
            destination: Destination city
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            rooms: Number of rooms
            star_rating: Star rating filter (1-5)
            max_price: Maximum price per night
            
        Returns:
            Dictionary with hotel results
        """
        try:
            # Calculate number of nights
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (check_out_date - check_in_date).days
            
            # Get mock hotels
            hotels = self._get_mock_hotels(
                destination,
                star_rating,
                max_price,
                nights
            )
            
            return {
                "success": True,
                "hotels": hotels,
                "search_criteria": {
                    "destination": destination,
                    "check_in": check_in,
                    "check_out": check_out,
                    "nights": nights,
                    "guests": guests,
                    "rooms": rooms
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "hotels": []
            }
    
    def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Get detailed information about a hotel"""
        return {
            "hotel_id": hotel_id,
            "name": "Luxury Grand Hotel",
            "star_rating": 5,
            "address": "123 Main Street, Dubai",
            "description": "Luxurious 5-star hotel with world-class amenities",
            "amenities": [
                "Free WiFi",
                "Swimming Pool",
                "Gym",
                "Spa",
                "Restaurant",
                "Room Service",
                "Airport Shuttle"
            ],
            "rooms": [
                {
                    "type": "Deluxe Room",
                    "price": 5000,
                    "max_guests": 2,
                    "features": ["King Bed", "City View", "Mini Bar"]
                },
                {
                    "type": "Suite",
                    "price": 8000,
                    "max_guests": 4,
                    "features": ["2 Bedrooms", "Ocean View", "Balcony", "Living Room"]
                }
            ],
            "reviews": {
                "rating": 4.5,
                "count": 1250,
                "highlights": ["Excellent location", "Great service", "Clean rooms"]
            }
        }
    
    def check_availability(
        self,
        hotel_id: str,
        check_in: str,
        check_out: str,
        rooms: int
    ) -> Dict[str, Any]:
        """Check hotel room availability"""
        return {
            "hotel_id": hotel_id,
            "available": True,
            "rooms_available": 15,
            "can_book": rooms <= 15,
            "price_per_night": 5000
        }
    
    def _get_google_maps_link(self, hotel_name: str, destination: str) -> str:
        """Generate Google Maps search link for a hotel"""
        import urllib.parse
        query = f"{hotel_name}, {destination}"
        encoded_query = urllib.parse.quote(query)
        return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
    
    def _get_static_map_url(self, hotel_name: str, destination: str, google_maps_api_key: str = None) -> str:
        """Generate Google Static Maps API URL for hotel location"""
        import urllib.parse
        
        # If no API key provided, return a placeholder
        if not google_maps_api_key:
            google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY")
        
        location = f"{hotel_name}, {destination}"
        encoded_location = urllib.parse.quote(location)
        
        # Generate static map URL
        return f"https://maps.googleapis.com/maps/api/staticmap?center={encoded_location}&zoom=15&size=400x200&markers=color:red%7C{encoded_location}&key={google_maps_api_key}"
    
    def _get_mock_hotels(
        self,
        destination: str,
        star_rating: Optional[int],
        max_price: Optional[float],
        nights: int
    ) -> List[Dict[str, Any]]:
        """Generate mock hotel data with Google Maps integration"""
        
        # City-specific coordinates and addresses
        city_coordinates = {
            "dubai": {"lat": 25.2048, "lng": 55.2708},
            "riyadh": {"lat": 24.7136, "lng": 46.6753},
            "jeddah": {"lat": 21.5433, "lng": 39.1728},
            "mecca": {"lat": 21.4225, "lng": 39.8262},
            "medina": {"lat": 24.5247, "lng": 39.5692},
            "paris": {"lat": 48.8566, "lng": 2.3522},
            "london": {"lat": 51.5074, "lng": -0.1278},
            "new york": {"lat": 40.7128, "lng": -74.0060},
            "mumbai": {"lat": 19.0760, "lng": 72.8777},
            "bangalore": {"lat": 12.9716, "lng": 77.5946}
        }
        
        # Get coordinates for destination
        dest_lower = destination.lower()
        base_coords = city_coordinates.get(dest_lower, {"lat": 25.0, "lng": 55.0})
        
        hotels_data = [
            {
                "name": "Grand Palace Hotel",
                "star_rating": 5,
                "base_price": 8000,
                "location": "City Center",
                "address": f"123 Main Boulevard, {destination}",
                "coordinates": {"lat": base_coords["lat"] + 0.01, "lng": base_coords["lng"] + 0.01}
            },
            {
                "name": "Comfort Inn",
                "star_rating": 3,
                "base_price": 3000,
                "location": "Near Airport",
                "address": f"456 Airport Road, {destination}",
                "coordinates": {"lat": base_coords["lat"] - 0.02, "lng": base_coords["lng"] + 0.03}
            },
            {
                "name": "Business Suites",
                "star_rating": 4,
                "base_price": 5000,
                "location": "Business District",
                "address": f"789 Corporate Avenue, {destination}",
                "coordinates": {"lat": base_coords["lat"] + 0.015, "lng": base_coords["lng"] - 0.01}
            },
            {
                "name": "Budget Stay",
                "star_rating": 2,
                "base_price": 1500,
                "location": "Suburbs",
                "address": f"321 Residential Street, {destination}",
                "coordinates": {"lat": base_coords["lat"] - 0.03, "lng": base_coords["lng"] - 0.02}
            },
            {
                "name": "Luxury Resort & Spa",
                "star_rating": 5,
                "base_price": 12000,
                "location": "Beachfront",
                "address": f"555 Coastal Drive, {destination}",
                "coordinates": {"lat": base_coords["lat"] + 0.02, "lng": base_coords["lng"] + 0.025}
            }
        ]
        
        hotels = []
        
        for i, data in enumerate(hotels_data):
            # Apply filters
            if star_rating and data["star_rating"] != star_rating:
                continue
            
            if max_price and data["base_price"] > max_price:
                continue
            
            price_per_night = data["base_price"]
            total_price = price_per_night * nights
            
            # Simple hotel data - just name, price, and Google Maps link
            hotel = {
                "hotel_id": f"HOTEL_{destination.upper()}_{i+1}",
                "name": data["name"],
                "star_rating": data["star_rating"],
                "price_per_night": price_per_night,
                "total_price": total_price,
                "currency": "INR",
                "google_maps_link": self._get_google_maps_link(data["name"], destination),
                # Rich text format for display - one line clickable link
                "display_text": f"🏨 {data['name']} ({'⭐' * data['star_rating']}) - ₹{price_per_night:,}/night",
                "coordinates": data.get("coordinates", {"lat": base_coords["lat"], "lng": base_coords["lng"]})
            }
            
            hotels.append(hotel)
        
        return sorted(hotels, key=lambda x: x["star_rating"], reverse=True)[:5]
    
    def _get_amenities(self, star_rating: int) -> List[str]:
        """Get amenities based on star rating"""
        base_amenities = ["WiFi", "Air Conditioning", "TV"]
        
        if star_rating >= 3:
            base_amenities.extend(["Restaurant", "Room Service"])
        
        if star_rating >= 4:
            base_amenities.extend(["Gym", "Swimming Pool", "Spa"])
        
        if star_rating >= 5:
            base_amenities.extend(["Concierge", "Butler Service", "Valet Parking"])
        
        return base_amenities


if __name__ == "__main__":
    # Test the Hotel API
    api = HotelAPI()
    
    print("Testing Hotel API...\n")
    
    # Test hotel search
    print("1. Searching hotels in Dubai")
    results = api.search_hotels(
        destination="Dubai",
        check_in="2025-12-10",
        check_out="2025-12-15",
        guests=2,
        rooms=1
    )
    
    if results["success"]:
        print(f"✅ Found {len(results['hotels'])} hotels")
        for hotel in results['hotels'][:3]:
            print(f"   {hotel['name']} ({hotel['star_rating']}⭐): ₹{hotel['price_per_night']}/night")
    else:
        print(f"❌ Error: {results['error']}")
    
    print("\n2. Getting hotel details")
    details = api.get_hotel_details("HOTEL_DUBAI_1")
    print(f"✅ Hotel: {details['name']}")
    print(f"   Rating: {details['star_rating']}⭐")
    
    print("\n✅ Hotel API test completed")

