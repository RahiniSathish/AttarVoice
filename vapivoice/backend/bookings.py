"""
Booking Service - Manages all booking operations
Coordinates between flight/hotel APIs and customer bookings
"""

import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import string
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BookingService:
    """Main booking service for flights and hotels"""
    
    def __init__(self, db_path: str = "bookings.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for bookings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id TEXT PRIMARY KEY,
                booking_reference TEXT UNIQUE,
                booking_type TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                item_id TEXT,
                booking_data TEXT,
                total_amount REAL,
                currency TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Create passengers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passengers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT,
                first_name TEXT,
                last_name TEXT,
                date_of_birth TEXT,
                passport_number TEXT,
                nationality TEXT,
                FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_booking(
        self,
        booking_type: str,
        item_id: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        passenger_details: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create a new booking
        
        Args:
            booking_type: Type of booking (flight, hotel, package)
            item_id: ID of the flight/hotel to book
            customer_phone: Customer phone number
            customer_email: Customer email
            passenger_details: List of passenger details
            
        Returns:
            Booking confirmation details
        """
        try:
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            booking_id = f"BK_{datetime.now().strftime('%Y%m%d')}_{booking_reference}"
            
            # Get item details and calculate amount
            if booking_type == "flight":
                item_data = self._get_flight_booking_data(item_id)
            elif booking_type == "hotel":
                item_data = self._get_hotel_booking_data(item_id)
            else:
                return {
                    "success": False,
                    "error": "Invalid booking type"
                }
            
            if not item_data:
                return {
                    "success": False,
                    "error": "Item not found"
                }
            
            total_amount = item_data.get("price", 0)
            
            # Save booking to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bookings (
                    booking_id, booking_reference, booking_type,
                    customer_phone, customer_email, item_id,
                    booking_data, total_amount, currency, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                booking_id,
                booking_reference,
                booking_type,
                customer_phone,
                customer_email or "",
                item_id,
                json.dumps(item_data),
                total_amount,
                "INR",
                "pending",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Save passenger details if provided
            if passenger_details:
                for passenger in passenger_details:
                    cursor.execute('''
                        INSERT INTO passengers (
                            booking_id, first_name, last_name,
                            date_of_birth, passport_number, nationality
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        booking_id,
                        passenger.get("first_name", ""),
                        passenger.get("last_name", ""),
                        passenger.get("date_of_birth", ""),
                        passenger.get("passport_number", ""),
                        passenger.get("nationality", "")
                    ))
            
            conn.commit()
            conn.close()
            
            # Send confirmation (SMS/Email)
            self._send_confirmation(booking_reference, customer_phone, customer_email)
            
            return {
                "success": True,
                "booking_id": booking_id,
                "booking_reference": booking_reference,
                "booking_type": booking_type,
                "total_amount": total_amount,
                "currency": "INR",
                "status": "pending",
                "payment_link": f"https://mytrip.ai/pay/{booking_reference}",
                "message": "Booking created successfully. Please complete payment."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_booking_status(self, booking_reference: str) -> Dict[str, Any]:
        """Get booking status by reference number"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM bookings WHERE booking_reference = ?
            ''', (booking_reference,))
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "success": False,
                    "error": "Booking not found"
                }
            
            # Get passenger details
            cursor.execute('''
                SELECT * FROM passengers WHERE booking_id = ?
            ''', (row[0],))
            
            passengers = []
            for p_row in cursor.fetchall():
                passengers.append({
                    "first_name": p_row[2],
                    "last_name": p_row[3],
                    "date_of_birth": p_row[4]
                })
            
            conn.close()
            
            booking_data = json.loads(row[6]) if row[6] else {}
            
            return {
                "success": True,
                "booking_reference": row[1],
                "booking_type": row[2],
                "status": row[9],
                "total_amount": row[7],
                "currency": row[8],
                "booking_details": booking_data,
                "passengers": passengers,
                "created_at": row[10]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_booking_status(self, booking_reference: str, status: str) -> bool:
        """Update booking status (pending, confirmed, completed)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE bookings
                SET status = ?, updated_at = ?
                WHERE booking_reference = ?
            ''', (status, datetime.now().isoformat(), booking_reference))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            return False
    
    def get_customer_bookings(self, customer_phone: str) -> List[Dict[str, Any]]:
        """Get all bookings for a customer"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM bookings WHERE customer_phone = ?
                ORDER BY created_at DESC
            ''', (customer_phone,))
            
            bookings = []
            for row in cursor.fetchall():
                bookings.append({
                    "booking_reference": row[1],
                    "booking_type": row[2],
                    "status": row[9],
                    "total_amount": row[7],
                    "created_at": row[10]
                })
            
            conn.close()
            
            return bookings
            
        except Exception as e:
            logger.error(f"Error fetching customer bookings: {e}")
            return []
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def _get_flight_booking_data(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get flight data for booking"""
        # In production, fetch from flight API
        return {
            "flight_id": flight_id,
            "airline": "IndiGo",
            "flight_number": "6E1234",
            "route": "BLR-DXB",
            "departure": "2025-12-10 08:30",
            "arrival": "2025-12-10 11:45",
            "price": 15000
        }
    
    def _get_hotel_booking_data(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get hotel data for booking"""
        return {
            "hotel_id": hotel_id,
            "hotel_name": "Grand Palace Hotel",
            "location": "Dubai",
            "check_in": "2025-12-10",
            "check_out": "2025-12-15",
            "nights": 5,
            "price": 25000
        }
    
    def _send_confirmation(
        self,
        booking_reference: str,
        phone: str,
        email: Optional[str]
    ):
        """Send booking confirmation via SMS/Email"""
        # SMS
        message = f"Travel.ai: Booking {booking_reference} created! Complete payment: https://mytrip.ai/pay/{booking_reference}"
        self._send_sms(phone, message)
        
        # Email (if provided)
        if email:
            self._send_email(email, booking_reference)
    
    def _send_sms(self, phone: str, message: str) -> None:
        """Send SMS (integrate with Twilio or similar)"""
        logger.info(f"SMS notification to {phone}: {message}")
        # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
    
    def _send_email(self, email: str, booking_reference: str) -> None:
        """Send email confirmation"""
        logger.info(f"Email notification to {email}: Booking {booking_reference}")
        # TODO: Integrate with email service


if __name__ == "__main__":
    # Test booking service
    service = BookingService()
    
    print("Testing Booking Service...\n")
    
    # 1. Create flight booking
    print("1. Creating flight booking")
    booking = service.create_booking(
        booking_type="flight",
        item_id="FLBLRDXB1",
        customer_phone="+919876543210",
        customer_email="customer@example.com",
        passenger_details=[
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01"
            }
        ]
    )
    
    if booking["success"]:
        print(f" Booking created: {booking['booking_reference']}")
        print(f"   Amount: ₹{booking['total_amount']}")
        print(f"   Payment: {booking['payment_link']}\n")
        
        # 2. Check booking status
        print("2. Checking booking status")
        status = service.get_booking_status(booking['booking_reference'])
        print(f" Status: {status['status']}\n")
        
        # 3. Update status to confirmed
        print("3. Updating status to confirmed")
        service.update_booking_status(booking['booking_reference'], "confirmed")
        status = service.get_booking_status(booking['booking_reference'])
        print(f" New status: {status['status']}\n")
        
    else:
        print(f" Error: {booking['error']}")
    
    print(" Booking service test completed")

