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
        
        # Determine if this is a Saudi Arabia route
        saudi_airports = ["RUH", "JED", "DMM", "MED", "AHB", "TIF", "TUU"]
        is_saudi_route = origin in saudi_airports or destination in saudi_airports
        
        # Select airlines based on route
        if is_saudi_route:
            airlines = ["Saudia", "Flynas", "Flyadeal"]
        else:
            airlines = ["IndiGo", "Air India", "Emirates", "Vistara", "SpiceJet"]
        
        base_price = self._calculate_base_price(origin, destination, cabin_class)
        
        # Determine currency
        currency = "SAR" if is_saudi_route else "INR"
        
        flights = []
        
        for i, airline in enumerate(airlines[:3]):  # Return top 3 flights
            departure_hour = 7 + (i * 4)  # 7am, 11am, 3pm
            arrival_hour = departure_hour + 2  # 2 hour flight
            
            flight = {
                "flight_id": f"FL{origin}{destination}{i+1}",
                "airline": airline,
                "flight_number": f"{self._get_airline_code(airline)}{500+i}",
                "origin": origin,
                "destination": destination,
                "departure_date": date,
                "departure_time": f"{departure_hour:02d}:30",
                "arrival_time": f"{arrival_hour:02d}:{'40' if i == 0 else '25'}",
                "duration": f"{2 if i < 2 else 2}h {10 + (i*5)}m",
                "stops": 0,  # All direct flights
                "cabin_class": cabin_class,
                "price": base_price + (i * 200),  # Varying prices
                "currency": currency,
                "seats_available": 42 - (i * 5),
                "baggage": {
                    "cabin": "7kg",
                    "checked": "15kg" if cabin_class == "economy" else "30kg"
                },
                "amenities": {
                    "wifi": airline in ["Emirates", "Saudia"] or i == 0,
                    "meal": cabin_class != "economy" or airline in ["Emirates", "Saudia"],
                    "entertainment": airline in ["Emirates", "Saudia"]
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
            # India routes (INR)
            ("BLR", "DXB"): 15000,
            ("BOM", "DXB"): 14000,
            ("DEL", "DXB"): 13000,
            ("BLR", "SIN"): 18000,
            ("BOM", "LHR"): 45000,
            ("DEL", "JFK"): 65000,
        }
        
        # Try both directions
        base = route_prices.get((origin, destination)) or route_prices.get((destination, origin), 1000)
        
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

