"""
Mock Flights Database - Always returns flights for testing
Static flight data that always works, no external API required
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MockFlightsDatabase:
    """Static flight database with guaranteed flight availability"""
    
    def __init__(self):
        self.flights_db = self._initialize_flights()
        logger.info(" Mock Flights Database initialized")
    
    def _initialize_flights(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize static flight database"""
        return {
            # Bangalore to Jeddah
            "BLR-JED": [
                {
                    "id": "BLR-JED-001",
                    "airline": "Air India Express",
                    "flight_number": "IX 881",
                    "origin": "Bangalore",
                    "destination": "Jeddah",
                    "from": {"code": "BLR", "time": "02:15"},
                    "to": {"code": "JED", "time": "05:30"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 28450,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 42,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-JED-002",
                    "airline": "IndiGo",
                    "flight_number": "6E 77",
                    "origin": "Bangalore",
                    "destination": "Jeddah",
                    "from": {"code": "BLR", "time": "03:55"},
                    "to": {"code": "JED", "time": "07:15"},
                    "duration": "5h 50m",
                    "stops": 0,
                    "price": 27890,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 38,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-JED-003",
                    "airline": "Air India",
                    "flight_number": "AI 969",
                    "origin": "Bangalore",
                    "destination": "Jeddah",
                    "from": {"code": "BLR", "time": "13:45"},
                    "to": {"code": "JED", "time": "17:00"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 29100,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 45,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-JED-004",
                    "airline": "Saudia",
                    "flight_number": "SV 759",
                    "origin": "Bangalore",
                    "destination": "Jeddah",
                    "from": {"code": "BLR", "time": "14:35"},
                    "to": {"code": "JED", "time": "17:50"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 31200,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 50,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-JED-005",
                    "airline": "Air India Express",
                    "flight_number": "IX 885",
                    "origin": "Bangalore",
                    "destination": "Jeddah",
                    "from": {"code": "BLR", "time": "21:10"},
                    "to": {"code": "JED", "time": "00:30"},
                    "duration": "5h 50m",
                    "stops": 0,
                    "price": 28950,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 40,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-JED-006",
                    "airline": "IndiGo",
                    "flight_number": "6E 73",
                    "origin": "Bangalore",
                    "destination": "Jeddah",
                    "from": {"code": "BLR", "time": "22:40"},
                    "to": {"code": "JED", "time": "02:00"},
                    "duration": "5h 50m",
                    "stops": 0,
                    "price": 27650,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 35,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                }
            ],
            
            # Bangalore to Riyadh
            "BLR-RUH": [
                {
                    "id": "BLR-RUH-001",
                    "airline": "Air India Express",
                    "flight_number": "IX 883",
                    "origin": "Bangalore",
                    "destination": "Riyadh",
                    "from": {"code": "BLR", "time": "02:00"},
                    "to": {"code": "RUH", "time": "05:10"},
                    "duration": "5h 40m",
                    "stops": 0,
                    "price": 27890,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 44,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-RUH-002",
                    "airline": "IndiGo",
                    "flight_number": "6E 65",
                    "origin": "Bangalore",
                    "destination": "Riyadh",
                    "from": {"code": "BLR", "time": "04:10"},
                    "to": {"code": "RUH", "time": "07:25"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 26950,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 40,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-RUH-003",
                    "airline": "Air India",
                    "flight_number": "AI 963",
                    "origin": "Bangalore",
                    "destination": "Riyadh",
                    "from": {"code": "BLR", "time": "09:25"},
                    "to": {"code": "RUH", "time": "12:35"},
                    "duration": "5h 40m",
                    "stops": 0,
                    "price": 28550,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 48,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-RUH-004",
                    "airline": "Saudia",
                    "flight_number": "SV 753",
                    "origin": "Bangalore",
                    "destination": "Riyadh",
                    "from": {"code": "BLR", "time": "15:00"},
                    "to": {"code": "RUH", "time": "18:15"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 30200,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 52,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-RUH-005",
                    "airline": "Air India Express",
                    "flight_number": "IX 887",
                    "origin": "Bangalore",
                    "destination": "Riyadh",
                    "from": {"code": "BLR", "time": "21:30"},
                    "to": {"code": "RUH", "time": "00:45"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 28100,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 38,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                },
                {
                    "id": "BLR-RUH-006",
                    "airline": "IndiGo",
                    "flight_number": "6E 61",
                    "origin": "Bangalore",
                    "destination": "Riyadh",
                    "from": {"code": "BLR", "time": "23:10"},
                    "to": {"code": "RUH", "time": "02:25"},
                    "duration": "5h 45m",
                    "stops": 0,
                    "price": 27200,
                    "currency": "INR",
                    "cabin_class": "Economy",
                    "seats_available": 36,
                    "baggage": {"checked": "30kg", "cabin": "7kg"}
                }
            ],
            
            # Bangalore to Dubai
            "BLR-DXB": [
                {"id": "BLR-DXB-001", "airline": "Emirates", "flight_number": "EK 501", "origin": "Bangalore", "destination": "Dubai", "from": {"code": "BLR", "time": "01:00"}, "to": {"code": "DXB", "time": "03:30"}, "duration": "4h 30m", "stops": 0, "price": 18500, "currency": "INR", "cabin_class": "Economy", "seats_available": 50, "baggage": {"checked": "23kg", "cabin": "7kg"}},
                {"id": "BLR-DXB-002", "airline": "Air India Express", "flight_number": "IX 431", "origin": "Bangalore", "destination": "Dubai", "from": {"code": "BLR", "time": "06:15"}, "to": {"code": "DXB", "time": "08:45"}, "duration": "4h 30m", "stops": 0, "price": 17900, "currency": "INR", "cabin_class": "Economy", "seats_available": 45, "baggage": {"checked": "23kg", "cabin": "7kg"}},
                {"id": "BLR-DXB-003", "airline": "IndiGo", "flight_number": "6E 91", "origin": "Bangalore", "destination": "Dubai", "from": {"code": "BLR", "time": "09:45"}, "to": {"code": "DXB", "time": "12:15"}, "duration": "4h 30m", "stops": 0, "price": 18200, "currency": "INR", "cabin_class": "Economy", "seats_available": 48, "baggage": {"checked": "23kg", "cabin": "7kg"}},
                {"id": "BLR-DXB-004", "airline": "Saudia", "flight_number": "SV 401", "origin": "Bangalore", "destination": "Dubai", "from": {"code": "BLR", "time": "13:20"}, "to": {"code": "DXB", "time": "15:50"}, "duration": "4h 30m", "stops": 0, "price": 19500, "currency": "INR", "cabin_class": "Economy", "seats_available": 52, "baggage": {"checked": "23kg", "cabin": "7kg"}},
                {"id": "BLR-DXB-005", "airline": "FlyDubai", "flight_number": "FZ 151", "origin": "Bangalore", "destination": "Dubai", "from": {"code": "BLR", "time": "16:00"}, "to": {"code": "DXB", "time": "18:30"}, "duration": "4h 30m", "stops": 0, "price": 17650, "currency": "INR", "cabin_class": "Economy", "seats_available": 40, "baggage": {"checked": "20kg", "cabin": "7kg"}},
                {"id": "BLR-DXB-006", "airline": "Air India", "flight_number": "AI 441", "origin": "Bangalore", "destination": "Dubai", "from": {"code": "BLR", "time": "19:30"}, "to": {"code": "DXB", "time": "22:00"}, "duration": "4h 30m", "stops": 0, "price": 19800, "currency": "INR", "cabin_class": "Economy", "seats_available": 46, "baggage": {"checked": "23kg", "cabin": "7kg"}}
            ]
        }
    
    def _normalize_city(self, city: str) -> str:
        """Normalize city names to airport codes"""
        city_mappings = {
            "bangalore": "BLR",
            "bengaluru": "BLR",
            "blr": "BLR",
            "jeddah": "JED",
            "jed": "JED",
            "riyadh": "RUH",
            "ruh": "RUH",
            # Additional cities
            "mumbai": "BOM",
            "bombay": "BOM",
            "bom": "BOM",
            "delhi": "DEL",
            "new delhi": "DEL",
            "del": "DEL",
            "dubai": "DXB",
            "dxb": "DXB",
            "goa": "GOI",
            "goi": "GOI",
            "hyderabad": "HYD",
            "hyd": "HYD",
            "kolkata": "CCU",
            "calcutta": "CCU",
            "ccu": "CCU",
            "pune": "PNQ",
            "pnq": "PNQ",
            "kochi": "COK",
            "cochin": "COK",
            "cok": "COK",
            "singapore": "SIN",
            "sin": "SIN",
            "bangkok": "BKK",
            "bkk": "BKK",
            "london": "LHR",
            "lhr": "LHR",
            "paris": "CDG",
            "cdg": "CDG",
            "new york": "JFK",
            "jfk": "JFK",
            "los angeles": "LAX",
            "lax": "LAX",
            "tokyo": "NRT",
            "nrt": "NRT",
            "sydney": "SYD",
            "syd": "SYD",
            "auckland": "AKL",
            "akl": "AKL",
        }
        return city_mappings.get(city.lower(), city.upper())
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        passengers: int = 1,
        cabin_class: str = "economy"
    ) -> Dict[str, Any]:
        """
        Search for flights in the mock database
        Always returns flights for supported routes
        """
        try:
            # Normalize city names
            origin_code = self._normalize_city(origin)
            dest_code = self._normalize_city(destination)
            route_key = f"{origin_code}-{dest_code}"
            
            logger.info(f" Mock DB Search: {origin} ({origin_code}) → {destination} ({dest_code})")
            logger.info(f"📅 Date: {departure_date}, Passengers: {passengers}, Class: {cabin_class}")
            
            # Check if route exists in database, if not generate dynamic flights
            if route_key not in self.flights_db:
                logger.warning(f" Route {route_key} not in mock database - generating dynamic flights")
                flights = self._generate_dynamic_flights(origin, destination, origin_code, dest_code)
            else:
                # Get flights for this route
                flights = self.flights_db[route_key].copy()
            
            # Add the departure date to each flight
            for flight in flights:
                flight["date"] = departure_date
                flight["departure_date"] = departure_date
                
                # Add dynamic fields
                flight["origin"] = origin
                flight["destination"] = destination
                flight["departure_time"] = flight["from"]["time"]
                flight["arrival_time"] = flight["to"]["time"]
                flight["flight_id"] = flight["id"]
            
            logger.info(f" Found {len(flights)} flights for route {route_key}")
            
            return {
                "success": True,
                "outbound_flights": flights,
                "return_flights": [],
                "search_criteria": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "passengers": passengers,
                    "cabin_class": cabin_class
                },
                "data_source": "mock_db",
                "message": f"Found {len(flights)} flights from {origin} to {destination}"
            }
            
        except Exception as e:
            logger.error(f" Error in mock flight search: {e}")
            return {
                "success": False,
                "message": "Error searching flights",
                "outbound_flights": [],
                "return_flights": [],
                "error": str(e),
                "data_source": "mock_db"
            }
    
    def _generate_dynamic_flights(self, origin: str, destination: str, origin_code: str, dest_code: str) -> List[Dict[str, Any]]:
        """
        Generate dynamic flight data for ANY city pair
        This ensures the mock database ALWAYS returns flights, even for unsupported routes
        """
        airlines = [
            {"name": "Air India", "code": "AI"},
            {"name": "IndiGo", "code": "6E"},
            {"name": "Emirates", "code": "EK"},
            {"name": "Qatar Airways", "code": "QR"},
            {"name": "Lufthansa", "code": "LH"},
            {"name": "British Airways", "code": "BA"}
        ]
        
        # Generate 6 flights with different times and prices
        flights = []
        base_price = 25000
        times = [
            ("02:00", "05:30", "5h 30m"),
            ("06:15", "09:45", "5h 30m"),
            ("09:30", "13:00", "5h 30m"),
            ("13:45", "17:15", "5h 30m"),
            ("18:00", "21:30", "5h 30m"),
            ("22:15", "01:45", "5h 30m")
        ]
        
        for i, (airline, (dep_time, arr_time, duration)) in enumerate(zip(airlines, times)):
            price_variation = (i * 1500) + (i % 2 * 500)
            flight = {
                "id": f"{origin_code}-{dest_code}-{i+1:03d}",
                "airline": airline["name"],
                "flight_number": f"{airline['code']} {100 + i}",
                "origin": origin,
                "destination": destination,
                "from": {"code": origin_code, "time": dep_time},
                "to": {"code": dest_code, "time": arr_time},
                "duration": duration,
                "stops": 0 if i < 4 else 1,  # First 4 are non-stop
                "price": base_price + price_variation,
                "currency": "INR",
                "cabin_class": "Economy",
                "seats_available": 30 + (i * 5),
                "baggage": {"checked": "30kg", "cabin": "7kg"},
                "departure_time": dep_time,
                "arrival_time": arr_time
            }
            flights.append(flight)
        
        logger.info(f"✨ Generated {len(flights)} dynamic flights for {origin} → {destination}")
        return flights

