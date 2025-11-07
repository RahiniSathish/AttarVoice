"""
Flight API - Flight Search and Booking Backend
Integrates with flight data providers (AviationStack, Amadeus, etc.)
"""

import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class FlightAPI:
    """Flight search and booking API"""
    
    def __init__(self):
        self.api_key = os.getenv("FLIGHT_API_KEY")
        self.api_url = os.getenv("FLIGHT_API_URL", "https://api.aviationstack.com/v1")
        self.timeout = 30
    
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
            origin: Origin airport code (BLR, BOM, etc.)
            destination: Destination airport code
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date (optional for one-way)
            passengers: Number of passengers
            cabin_class: Cabin class (economy, business, first)
            
        Returns:
            Dictionary with flight results
        """
        try:
            # For demo purposes, return mock data
            # In production, integrate with real flight API
            
            flights = self._get_mock_flights(
                origin,
                destination,
                departure_date,
                passengers,
                cabin_class
            )
            
            # If round trip, also get return flights
            return_flights = []
            if return_date:
                return_flights = self._get_mock_flights(
                    destination,
                    origin,
                    return_date,
                    passengers,
                    cabin_class
                )
            
            return {
                "success": True,
                "outbound_flights": flights,
                "return_flights": return_flights if return_date else [],
                "search_criteria": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "passengers": passengers,
                    "cabin_class": cabin_class
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "flights": []
            }
    
    def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific flight"""
        # Mock implementation
        return {
            "flight_id": flight_id,
            "airline": "IndiGo",
            "flight_number": "6E1234",
            "aircraft": "Airbus A320",
            "departure": {
                "airport": "BLR",
                "time": "08:30",
                "terminal": "1"
            },
            "arrival": {
                "airport": "DXB",
                "time": "11:45",
                "terminal": "2"
            },
            "duration": "3h 15m",
            "stops": 0,
            "baggage": {
                "cabin": "7kg",
                "checked": "15kg"
            }
        }
    
    def check_availability(self, flight_id: str, passengers: int) -> Dict[str, Any]:
        """Check if seats are available on a flight"""
        # Mock implementation
        return {
            "flight_id": flight_id,
            "available": True,
            "seats_remaining": 42,
            "can_book": passengers <= 42
        }
    
    def _get_mock_flights(
        self,
        origin: str,
        destination: str,
        date: str,
        passengers: int,
        cabin_class: str
    ) -> List[Dict[str, Any]]:
        """Generate mock flight data for demo purposes"""
        
        # Normalize airport codes and city names
        origin_upper = origin.upper()
        destination_upper = destination.upper()
        
        # Map city names to airport codes
        city_to_code = {
            "BANGALORE": "BLR",
            "BENGALURU": "BLR",
            "JEDDAH": "JED",
            "MUMBAI": "BOM",
            "DELHI": "DEL",
            "DUBAI": "DXB",
            "RIYADH": "RUH"
        }
        
        # Convert to codes if city names
        origin_code = city_to_code.get(origin_upper, origin_upper)
        destination_code = city_to_code.get(destination_upper, destination_upper)
        
        # Determine if this is a Saudi Arabia route
        saudi_airports = ["RUH", "JED", "DMM", "MED", "AHB", "TIF", "TUU"]
        indian_airports = ["BLR", "BOM", "DEL", "MAA", "HYD", "CCU", "COK"]
        
        is_india_to_saudi = (origin_code in indian_airports and destination_code in saudi_airports)
        is_saudi_to_india = (origin_code in saudi_airports and destination_code in indian_airports)
        is_saudi_route = destination_code in saudi_airports or origin_code in saudi_airports
        
        # Select airlines based on route type
        if is_india_to_saudi or is_saudi_to_india:
            # India ↔ Saudi Arabia: Mix of Indian, Saudi, and Gulf airlines
            airlines = ["Emirates", "Saudia", "IndiGo", "Air India", "Flynas", "Etihad"]
            flight_duration_hours = 5  # ~5 hours for India to Saudi
        elif is_saudi_route:
            # Domestic Saudi routes
            airlines = ["Saudia", "Flynas", "Flyadeal"]
            flight_duration_hours = 2
        else:
            # Other international routes
            airlines = ["IndiGo", "Air India", "Emirates", "Vistara", "SpiceJet"]
            flight_duration_hours = 3
        
        base_price = self._calculate_base_price(origin_code, destination_code, cabin_class)
        
        # Determine currency based on origin
        if origin_code in indian_airports:
            currency = "INR"
        elif origin_code in saudi_airports:
            currency = "SAR"
        else:
            currency = "USD"
        
        flights = []
        
        # Generate more flights for better variety
        num_flights = min(len(airlines), 6)  # Show up to 6 flights
        
        for i, airline in enumerate(airlines[:num_flights]):
            # Stagger departure times throughout the day
            departure_hour = 6 + (i * 3)  # 6am, 9am, 12pm, 3pm, 6pm, 9pm
            if departure_hour >= 24:
                departure_hour = departure_hour - 24
            
            arrival_hour = departure_hour + flight_duration_hours
            if arrival_hour >= 24:
                arrival_hour = arrival_hour - 24
            
            # Calculate minutes for variety
            departure_minute = 30 if i % 2 == 0 else 15
            arrival_minute = 45 if i % 2 == 0 else 20
            
            flight = {
                "flight_id": f"FL{origin_code}{destination_code}{i+1}",
                "airline": airline,
                "flight_number": f"{self._get_airline_code(airline)}{500+i}",
                "origin": origin_code,
                "destination": destination_code,
                "departure_date": date,
                "departure_time": f"{departure_hour:02d}:{departure_minute:02d}",
                "arrival_time": f"{arrival_hour:02d}:{arrival_minute:02d}",
                "duration": f"{flight_duration_hours}h {15 + (i*5)}m",
                "stops": 0 if i < 4 else 1,  # First 4 are direct, rest have stops
                "cabin_class": cabin_class,
                "price": base_price + (i * 150),  # Varying prices
                "currency": currency,
                "seats_available": 45 - (i * 3),
                "baggage": {
                    "cabin": "7kg",
                    "checked": "23kg" if cabin_class == "economy" else "32kg"
                },
                "amenities": {
                    "wifi": airline in ["Emirates", "Saudia", "Etihad", "Air India"],
                    "meal": True if cabin_class != "economy" or airline in ["Emirates", "Saudia", "Etihad"] else False,
                    "entertainment": airline in ["Emirates", "Saudia", "Etihad"]
                }
            }
            
            flights.append(flight)
        
        return flights
    
    def _calculate_base_price(self, origin: str, destination: str, cabin_class: str) -> float:
        """Calculate base price for a route"""
        
        # Distance-based pricing (simplified)
        route_prices = {
            # Saudi domestic routes (SAR)
            ("RUH", "JED"): 500,
            ("RUH", "DMM"): 400,
            ("JED", "DMM"): 450,
            ("RUH", "AHB"): 600,
            ("JED", "MED"): 400,
            # Saudi to UAE
            ("RUH", "DXB"): 800,
            ("JED", "DXB"): 850,
            ("RUH", "AUH"): 750,
            # Saudi to other GCC
            ("RUH", "DOH"): 600,
            ("RUH", "BAH"): 500,
            ("RUH", "KWI"): 650,
            # India to Saudi Arabia (INR)
            ("BLR", "JED"): 28000,
            ("BOM", "JED"): 26000,
            ("DEL", "JED"): 27000,
            ("BLR", "RUH"): 30000,
            ("BOM", "RUH"): 28000,
            ("DEL", "RUH"): 29000,
            # India to UAE (INR)
            ("BLR", "DXB"): 15000,
            ("BOM", "DXB"): 14000,
            ("DEL", "DXB"): 13000,
            # Other India routes (INR)
            ("BLR", "SIN"): 18000,
            ("BOM", "LHR"): 45000,
            ("DEL", "JFK"): 65000,
        }
        
        # Try both directions
        base = route_prices.get((origin, destination)) or route_prices.get((destination, origin), 25000)
        
        # Class multiplier
        class_multiplier = {
            "economy": 1.0,
            "premium_economy": 1.5,
            "business": 3.0,
            "first": 5.0
        }
        
        return base * class_multiplier.get(cabin_class, 1.0)
    
    def _get_airline_code(self, airline: str) -> str:
        """Get airline code"""
        codes = {
            # Saudi airlines
            "Saudia": "SV",
            "Flynas": "XY",
            "Flyadeal": "F3",
            # Indian airlines
            "IndiGo": "6E",
            "Air India": "AI",
            "Vistara": "UK",
            "SpiceJet": "SG",
            # International
            "Emirates": "EK",
            "Etihad": "EY",
            "Qatar Airways": "QR",
        }
        return codes.get(airline, "XX")


# Real API Integration (commented out - enable when API keys are available)

class RealFlightAPI(FlightAPI):
    """
    Real flight API integration with AviationStack or Amadeus
    Uncomment and configure when ready to use real data
    """
    
    def search_flights_real(self, **kwargs):
        """
        Real API call to AviationStack or Amadeus
        
        # AviationStack example:
        params = {
            'access_key': self.api_key,
            'dep_iata': origin,
            'arr_iata': destination,
            'flight_date': departure_date
        }
        
        response = requests.get(
            f"{self.api_url}/flights",
            params=params,
            timeout=self.timeout
        )
        
        return response.json()
        """
        pass


if __name__ == "__main__":
    # Test the Flight API
    api = FlightAPI()
    
    print("Testing Flight API...\n")
    
    # Test flight search
    print("1. Searching flights: BLR → DXB")
    results = api.search_flights(
        origin="BLR",
        destination="DXB",
        departure_date="2025-12-10",
        return_date="2025-12-15",
        passengers=1,
        cabin_class="economy"
    )
    
    if results["success"]:
        print(f"✅ Found {len(results['outbound_flights'])} outbound flights")
        for flight in results['outbound_flights']:
            print(f"   {flight['airline']} {flight['flight_number']}: ₹{flight['price']}")
        
        if results['return_flights']:
            print(f"✅ Found {len(results['return_flights'])} return flights")
    else:
        print(f"❌ Error: {results['error']}")
    
    print("\n2. Getting flight details")
    details = api.get_flight_details("FLBLRDXB1")
    print(f"✅ Flight: {details['airline']} {details['flight_number']}")
    print(f"   Duration: {details['duration']}, Stops: {details['stops']}")
    
    print("\n3. Checking availability")
    availability = api.check_availability("FLBLRDXB1", 2)
    print(f"✅ Available: {availability['available']}, Seats: {availability['seats_remaining']}")
    
    print("\n✅ Flight API test completed")

