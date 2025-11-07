"""
Mock Hotels Database - Provides demo hotel data for testing
Similar to mock_flights.py but for hotels
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MockHotelsDatabase:
    """Mock database with pre-defined hotel data for Saudi Arabia cities"""
    
    def __init__(self):
        self.hotels_data = {
            "Riyadh": [
                {
                    "id": "hotel_riyadh_001",
                    "name": "Four Seasons Hotel Riyadh",
                    "city": "Riyadh",
                    "location": "King Fahd Road, Riyadh",
                    "type": "5-star Luxury",
                    "stars": 5,
                    "price": "SAR 800-1,500/night",
                    "reviews": "World-class amenities, exceptional service, spa, and fine dining",
                    "google_maps_url": "https://www.google.com/maps/place/Four+Seasons+Hotel+Riyadh/@24.7722,46.6963,15z"
                },
                {
                    "id": "hotel_riyadh_002",
                    "name": "Ritz-Carlton Riyadh",
                    "city": "Riyadh",
                    "location": "King Fahd Road, Riyadh",
                    "type": "5-star Luxury",
                    "stars": 5,
                    "price": "SAR 1,100/night",
                    "reviews": "Premium luxury, elegant rooms, perfect for business travelers",
                    "google_maps_url": "https://www.google.com/maps/place/Ritz+Carlton+Riyadh/@24.7655,46.6931,15z"
                },
                {
                    "id": "hotel_riyadh_003",
                    "name": "Al Faisaliah Hotel",
                    "city": "Riyadh",
                    "location": "Al Faisaliah Tower, Olaya Street, Riyadh",
                    "type": "5-star",
                    "stars": 5,
                    "price": "SAR 950/night",
                    "reviews": "Iconic tower hotel, stunning views, excellent restaurants",
                    "google_maps_url": "https://www.google.com/maps/place/Al+Faisaliah+Hotel+Riyadh/@24.7722,46.6963,15z"
                },
                {
                    "id": "hotel_riyadh_004",
                    "name": "Hilton Riyadh",
                    "city": "Riyadh",
                    "location": "Olaya Street, Riyadh",
                    "type": "4-star",
                    "stars": 4,
                    "price": "SAR 600-800/night",
                    "reviews": "Great location, good amenities, excellent customer service",
                    "google_maps_url": "https://www.google.com/maps/place/Hilton+Riyadh/@24.7655,46.6931,15z"
                },
                {
                    "id": "hotel_riyadh_005",
                    "name": "Marriott Riyadh",
                    "city": "Riyadh",
                    "location": "King Abdul Aziz Road, Riyadh",
                    "type": "4-star",
                    "stars": 4,
                    "price": "SAR 550-700/night",
                    "reviews": "Comfortable rooms, good restaurants, professional staff",
                    "google_maps_url": "https://www.google.com/maps/place/Marriott+Riyadh/@24.7500,46.7000,15z"
                },
                {
                    "id": "hotel_riyadh_006",
                    "name": "InterContinental Riyadh",
                    "city": "Riyadh",
                    "location": "Corniche Street, Riyadh",
                    "type": "4-star",
                    "stars": 4,
                    "price": "SAR 500-650/night",
                    "reviews": "Beautiful views, spacious rooms, great facilities",
                    "google_maps_url": "https://www.google.com/maps/place/InterContinental+Riyadh/@24.7400,46.6800,15z"
                }
            ],
            "Jeddah": [
                {
                    "id": "hotel_jeddah_001",
                    "name": "Radisson Blu Jeddah",
                    "city": "Jeddah",
                    "location": "Red Sea Street, Jeddah",
                    "type": "5-star",
                    "stars": 5,
                    "price": "SAR 900-1,200/night",
                    "reviews": "Beachfront luxury, stunning Red Sea views, excellent dining",
                    "google_maps_url": "https://www.google.com/maps/place/Radisson+Blu+Jeddah/@21.5433,39.1727,15z"
                },
                {
                    "id": "hotel_jeddah_002",
                    "name": "Hilton Jeddah",
                    "city": "Jeddah",
                    "location": "Al Bahr Street, Jeddah",
                    "type": "4-star",
                    "stars": 4,
                    "price": "SAR 650-850/night",
                    "reviews": "Prime location near beaches, modern amenities, good value",
                    "google_maps_url": "https://www.google.com/maps/place/Hilton+Jeddah/@21.5400,39.1700,15z"
                },
                {
                    "id": "hotel_jeddah_003",
                    "name": "Movenpick Hotel Jeddah",
                    "city": "Jeddah",
                    "location": "Corniche, Jeddah",
                    "type": "4-star",
                    "stars": 4,
                    "price": "SAR 600-800/night",
                    "reviews": "Beautiful waterfront setting, comfortable rooms, friendly staff",
                    "google_maps_url": "https://www.google.com/maps/place/Movenpick+Jeddah/@21.5350,39.1650,15z"
                },
                {
                    "id": "hotel_jeddah_004",
                    "name": "Sheraton Jeddah",
                    "city": "Jeddah",
                    "location": "Al Hamra Street, Jeddah",
                    "type": "3-star",
                    "stars": 3,
                    "price": "SAR 400-550/night",
                    "reviews": "Budget-friendly, decent facilities, central location",
                    "google_maps_url": "https://www.google.com/maps/place/Sheraton+Jeddah/@21.5300,39.1600,15z"
                }
            ],
            "Al-Ula": [
                {
                    "id": "hotel_alula_001",
                    "name": "Maraya Concert Hall Hotel",
                    "city": "Al-Ula",
                    "location": "Al-Ula Desert, Saudi Arabia",
                    "type": "5-star Unique",
                    "stars": 5,
                    "price": "SAR 1,200-1,800/night",
                    "reviews": "Architectural marvel, luxury desert experience, UNESCO site nearby",
                    "google_maps_url": "https://www.google.com/maps/place/Maraya+Concert+Hall/@26.5882,37.9223,15z"
                },
                {
                    "id": "hotel_alula_002",
                    "name": "Habitas Al-Ula",
                    "city": "Al-Ula",
                    "location": "Al-Ula Desert, Saudi Arabia",
                    "type": "4-star Resort",
                    "stars": 4,
                    "price": "SAR 800-1,000/night",
                    "reviews": "Luxury desert resort, sustainable design, adventure activities",
                    "google_maps_url": "https://www.google.com/maps/place/Habitas+Al-Ula/@26.5900,37.9200,15z"
                },
                {
                    "id": "hotel_alula_003",
                    "name": "Al-Ula Oasis Hotel",
                    "city": "Al-Ula",
                    "location": "Al-Ula Town Center",
                    "type": "3-star",
                    "stars": 3,
                    "price": "SAR 400-600/night",
                    "reviews": "Comfortable, good base for exploring heritage sites",
                    "google_maps_url": "https://www.google.com/maps/place/Al-Ula+Oasis+Hotel/@26.5850,37.9100,15z"
                }
            ],
            "Abha": [
                {
                    "id": "hotel_abha_001",
                    "name": "Abha Palace Hotel",
                    "city": "Abha",
                    "location": "Mountain Road, Abha",
                    "type": "4-star",
                    "stars": 4,
                    "price": "SAR 550-750/night",
                    "reviews": "Cool mountain climate, scenic views, perfect for families",
                    "google_maps_url": "https://www.google.com/maps/place/Abha+Palace+Hotel/@18.2155,42.5053,15z"
                },
                {
                    "id": "hotel_abha_002",
                    "name": "Abha Heights Resort",
                    "city": "Abha",
                    "location": "Asir Mountain, Abha",
                    "type": "3-star",
                    "stars": 3,
                    "price": "SAR 400-550/night",
                    "reviews": "Budget hotel with great views, nature activities nearby",
                    "google_maps_url": "https://www.google.com/maps/place/Abha+Heights+Resort/@18.2100,42.5000,15z"
                }
            ],
            "Dammam": [
                {
                    "id": "hotel_dammam_001",
                    "name": "Intercontinental Dammam",
                    "city": "Dammam",
                    "location": "Corniche Road, Dammam",
                    "type": "5-star",
                    "stars": 5,
                    "price": "SAR 700-1,000/night",
                    "reviews": "Business hub, excellent amenities, beachfront location",
                    "google_maps_url": "https://www.google.com/maps/place/InterContinental+Dammam/@26.4159,50.0973,15z"
                },
                {
                    "id": "hotel_dammam_002",
                    "name": "Al Hamra Palace Hotel",
                    "city": "Dammam",
                    "location": "King Road, Dammam",
                    "type": "3-star",
                    "stars": 3,
                    "price": "SAR 350-500/night",
                    "reviews": "Affordable, clean rooms, convenient location",
                    "google_maps_url": "https://www.google.com/maps/place/Al+Hamra+Palace+Hotel/@26.4100,50.0900,15z"
                }
            ]
        }
        logger.info(" Mock Hotels Database initialized")
        logger.info(f"📊 Available cities: {list(self.hotels_data.keys())}")
        for city, hotels in self.hotels_data.items():
            logger.info(f"   - {city}: {len(hotels)} hotels")
    
    def search_hotels(self, city: str) -> Dict[str, Any]:
        """
        Search for hotels in a specific city
        
        Args:
            city (str): City name (Riyadh, Jeddah, Al-Ula, Abha, Dammam)
            
        Returns:
            Dict with success status and hotel list
        """
        try:
            # Normalize city name
            city_normalized = city.strip().lower()
            
            # Find matching city (case-insensitive)
            matching_city = None
            for db_city in self.hotels_data.keys():
                if db_city.lower() == city_normalized:
                    matching_city = db_city
                    break
            
            if not matching_city:
                logger.warning(f" City '{city}' not found in database")
                logger.info(f" Available cities: {', '.join(self.hotels_data.keys())}")
                return {
                    "success": False,
                    "message": f"Hotels for '{city}' not found. Available: Riyadh, Jeddah, Al-Ula, Abha, Dammam",
                    "hotels": []
                }
            
            hotels = self.hotels_data[matching_city]
            logger.info(f" Found {len(hotels)} hotels in {matching_city}")
            
            return {
                "success": True,
                "message": f"Found {len(hotels)} hotels in {matching_city}",
                "city": matching_city,
                "hotels": hotels,
                "total": len(hotels)
            }
            
        except Exception as e:
            logger.error(f" Error searching hotels: {e}")
            return {
                "success": False,
                "message": str(e),
                "hotels": []
            }
    
    def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific hotel"""
        try:
            for city_hotels in self.hotels_data.values():
                for hotel in city_hotels:
                    if hotel["id"] == hotel_id:
                        logger.info(f" Found hotel: {hotel['name']}")
                        return hotel
            
            logger.warning(f" Hotel '{hotel_id}' not found")
            return None
            
        except Exception as e:
            logger.error(f" Error getting hotel details: {e}")
            return None
    
    def get_all_cities(self) -> List[str]:
        """Get list of all available cities"""
        return list(self.hotels_data.keys())
    
    def get_city_hotel_count(self, city: str) -> int:
        """Get number of hotels in a city"""
        city_normalized = city.strip().lower()
        for db_city in self.hotels_data.keys():
            if db_city.lower() == city_normalized:
                return len(self.hotels_data[db_city])
        return 0


# Test the database
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    db = MockHotelsDatabase()
    
    # Test search
    print("\n🧪 Testing hotel search...")
    result = db.search_hotels("Riyadh")
    print(f" Result: {result['success']}, Hotels: {result['total']}")
    
    if result["success"]:
        print(f"\n📊 First hotel: {result['hotels'][0]}")
    
    print("\n Mock Hotels Database ready!")
