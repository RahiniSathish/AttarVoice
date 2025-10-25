"""
SMTP Email Service - Send emails using SMTP instead of SendGrid API
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    import os as os_module
    from pathlib import Path
    # Get the absolute path to .env file
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)
    logger.info(f"📄 Loaded .env from: {env_path}")
except ImportError:
    pass  # dotenv not installed, will use system env vars


class SMTPEmailService:
    """Service for sending emails via SMTP (SendGrid SMTP)"""
    
    def __init__(self):
        """Initialize SMTP client"""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME", "apikey")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@travel.ai")
        
        if not self.smtp_password:
            logger.warning("⚠️ SMTP_PASSWORD not configured in environment")
    
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            text_content: Plain text content
            html_content: Optional HTML formatted content
            
        Returns:
            bool: True if sent successfully
        """
        try:
            if not self.smtp_password:
                logger.error("❌ SMTP_PASSWORD not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach text and HTML parts
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)
            
            if html_content:
                part2 = MIMEText(html_content, 'html')
                msg.attach(part2)
            
            # Send email via SMTP
            logger.info(f"📧 Connecting to SMTP: {self.smtp_host}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.set_debuglevel(0)  # Set to 1 for debugging
                server.starttls()  # Enable TLS
                
                logger.info(f"🔐 Logging in as: {self.smtp_username}")
                server.login(self.smtp_username, self.smtp_password)
                
                logger.info(f"📤 Sending email to: {to_email}")
                server.send_message(msg)
                
                logger.info(f"✅ Email sent successfully to {to_email}")
                return True
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    
    def send_transcript_with_summary(
        self,
        to_email: str,
        user_name: str,
        summary: str,
        transcript: Optional[List[Dict]] = None,
        booking_details: Optional[Dict] = None,
        call_duration: Optional[int] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Send email with conversation summary and optional transcript
        
        Args:
            to_email: Recipient email address
            user_name: User's name
            summary: Conversation summary text
            transcript: Optional list of messages
            booking_details: Optional booking information
            call_duration: Optional call duration in seconds
            session_id: Optional session/call ID
            timestamp: Optional conversation timestamp
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Generate HTML content
            html_content = self._generate_html_email(
                user_name,
                summary,
                transcript,
                booking_details,
                call_duration,
                session_id,
                timestamp
            )
            
            # Generate plain text version
            text_content = self._generate_text_email(
                user_name,
                summary,
                transcript,
                call_duration,
                session_id,
                timestamp,
                booking_details
            )
            
            # Send email
            subject = "Your Attar Travel Conversation Summary"
            
            return self.send_email(
                to_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
        
        except Exception as e:
            logger.error(f"❌ Error in send_transcript_with_summary: {e}")
            return False
    
    
    def _generate_text_email(
        self,
        user_name: str,
        summary: str,
        transcript: Optional[List[Dict]] = None,
        call_duration: Optional[int] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        booking_details: Optional[Dict] = None
    ) -> str:
        """Generate plain text email"""
        
        lines = [
            f"Hello {user_name},",
            "",
            "Thank you for chatting with Attar Travel!",
            "Here's a summary of your recent conversation with our AI assistant.",
            "",
        ]
        
        # Add conversation details section
        if session_id or timestamp or transcript:
            lines.extend([
                "=" * 60,
                "CONVERSATION DETAILS",
                "=" * 60,
                "",
            ])
            
            if session_id:
                lines.append(f"• Session ID: {session_id}")
            
            if transcript:
                # Count only user and assistant messages (skip system)
                message_count = sum(1 for msg in transcript if msg.get("role", "").lower() != "system")
                lines.append(f"• Total messages: {message_count}")
            
            if timestamp:
                lines.append(f"• Call Date: {timestamp}")
            
            lines.extend(["", ""])
        
        lines.extend([
            "=" * 60,
            "CONVERSATION SUMMARY",
            "=" * 60,
            "",
            summary,
            "",
        ])
        
        if call_duration:
            try:
                # Convert to float first (handles int, float, and numeric strings)
                duration_seconds = float(call_duration)
                
                # Convert to integer seconds
                total_seconds = int(duration_seconds)
                
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                duration_text = f"{minutes} minutes {seconds} seconds"
            except (ValueError, TypeError):
                # If conversion fails, just display as string
                duration_text = str(call_duration)
            
            lines.extend([
                "=" * 60,
                "CALL DURATION",
                "=" * 60,
                "",
                duration_text,
                "",
            ])
        
        # Add booking details if available
        if booking_details:
            lines.extend([
                "=" * 60,
                "✈️ FLIGHT BOOKING CONFIRMATION",
                "=" * 60,
                "",
            ])
            
            airline = booking_details.get("airline", "Airlines")
            flight_number = booking_details.get("flight_number", "")
            departure_airport = booking_details.get("departure_location", booking_details.get("from", ""))
            arrival_airport = booking_details.get("destination", booking_details.get("to", ""))
            departure_time = booking_details.get("departure_time", "")
            arrival_time = booking_details.get("arrival_time", "")
            departure_date = booking_details.get("departure_date", "")
            duration = booking_details.get("duration", "")
            price = booking_details.get("price", booking_details.get("total_amount", "0"))
            currency = booking_details.get("currency", "₹")
            passengers = booking_details.get("num_travelers", booking_details.get("passengers", 1))
            service_class = booking_details.get("service_details", booking_details.get("class", "Economy"))
            return_date = booking_details.get("return_date", "")
            booking_id = booking_details.get("booking_id", "N/A")
            
            # Format price
            if isinstance(price, (int, float)):
                price_display = f"{currency}{price:,.0f}"
            else:
                price_display = f"{currency}{price}"
            
            lines.extend([
                f"AIRLINE: {airline} ({flight_number})",
                f"PRICE: {price_display}",
                f"PASSENGERS: {passengers} • CLASS: {service_class}",
                "",
                "OUTBOUND FLIGHT:",
                f"  {departure_date}",
                f"  {departure_airport} → {arrival_airport}",
                f"  Departure: {departure_time}",
                f"  Arrival: {arrival_time}",
                f"  Duration: {duration}",
                "",
            ])
            
            # Add return flight if exists
            if return_date:
                lines.extend([
                    "RETURN FLIGHT:",
                    f"  {return_date}",
                    f"  {arrival_airport} → {departure_airport}",
                    f"  Departure: {arrival_time}",
                    f"  Arrival: {departure_time}",
                    f"  Duration: {duration}",
                    "",
                ])
            
            lines.extend([
                f"BOOKING ID: {booking_id}",
                "STATUS: ✅ CONFIRMED",
                "",
            ])
        
        lines.extend([
            "=" * 60,
            "",
            "Best regards,",
            "Attar Travel Team",
            "",
            "Attar Travels",
            "Email: attartravel25@gmail.com",
        ])
        
        return "\n".join(lines)
    
    
    def _format_summary_html(self, summary: str) -> str:
        """
        Format the structured summary text into clean HTML with proper styling.
        Converts emoji headers and bullet points into styled HTML sections.
        """
        import re
        
        # Split summary into lines
        lines = summary.split('\n')
        html_parts = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header (starts with emoji)
            if line.startswith('📍') or line.startswith('🎯') or line.startswith('✅') or line.startswith('📝'):
                # Extract emoji and title, but only show title (remove emoji)
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    emoji, title = parts
                    html_parts.append(f'<div style="margin-top: 20px; margin-bottom: 10px;"><strong style="font-size: 16px; color: #1F2937;">{title}</strong></div>')
            elif line.startswith('•'):
                # Bullet point
                text = line[1:].strip()
                html_parts.append(f'<div style="margin-left: 20px; margin-bottom: 8px;">• {text}</div>')
            else:
                # Regular paragraph text
                html_parts.append(f'<div style="margin-bottom: 12px;">{line}</div>')
        
        return '\n'.join(html_parts)
    
    
    def _generate_booking_card_html(self, booking_details: Dict) -> str:
        """Generate beautiful flight booking card HTML matching the screenshot format"""
        
        # Extract booking details
        airline = booking_details.get("airline", "Airlines")
        flight_number = booking_details.get("flight_number", "")
        
        # Departure info
        departure_airport = booking_details.get("departure_location", booking_details.get("from", ""))
        departure_time = booking_details.get("departure_time", "")
        departure_date = booking_details.get("departure_date", "")
        
        # Arrival info
        arrival_airport = booking_details.get("destination", booking_details.get("to", ""))
        arrival_time = booking_details.get("arrival_time", "")
        
        # Flight details
        duration = booking_details.get("duration", "")
        price = booking_details.get("price", booking_details.get("total_amount", "0"))
        currency = booking_details.get("currency", "₹")
        passengers = booking_details.get("num_travelers", booking_details.get("passengers", 1))
        
        # Return flight info (if exists)
        return_date = booking_details.get("return_date", "")
        is_round_trip = bool(return_date)
        
        # Service class
        service_class = booking_details.get("service_details", booking_details.get("class", "Economy"))
        
        # Format price
        if isinstance(price, (int, float)):
            price_display = f"{currency}{price:,.0f}"
        else:
            price_display = f"{currency}{price}"
        
        # Build the HTML card
        html = f'''
        <div style="margin-bottom: 30px;">
            <h2 style="margin: 0 0 20px 0; color: #374151; font-size: 20px; font-weight: 600;">✈️ Flight Booking Confirmation</h2>
            
            <!-- Flight Card Container -->
            <div style="background: #FFFFFF; border: 2px solid #E5E7EB; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                
                <!-- Airline Header -->
                <div style="background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); padding: 15px 20px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <div style="width: 40px; height: 40px; background: #FFFFFF; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                            <span style="font-size: 20px;">✈️</span>
                        </div>
                        <div>
                            <div style="color: #FFFFFF; font-size: 18px; font-weight: 700; margin-bottom: 2px;">{airline}</div>
                            <div style="color: #FEE2E2; font-size: 12px;">{flight_number}</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #FFFFFF; font-size: 24px; font-weight: 700;">{price_display}</div>
                        <div style="color: #FEE2E2; font-size: 12px;">{passengers} passenger{'s' if passengers > 1 else ''} • {service_class}</div>
                    </div>
                </div>
                
                <!-- Outbound Flight -->
                <div style="padding: 25px 20px; border-bottom: 2px dashed #E5E7EB;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <div style="flex: 1;">
                            <div style="color: #9CA3AF; font-size: 12px; margin-bottom: 4px;">{departure_date}</div>
                            <div style="font-size: 28px; font-weight: 700; color: #1F2937; margin-bottom: 2px;">{departure_time}</div>
                            <div style="color: #14B8A6; font-size: 16px; font-weight: 600; background: #F0FDFA; padding: 4px 12px; border-radius: 6px; display: inline-block;">{departure_airport}</div>
                        </div>
                        
                        <div style="flex: 1; text-align: center; padding: 0 15px;">
                            <div style="color: #9CA3AF; font-size: 12px; margin-bottom: 6px;">{duration}</div>
                            <div style="position: relative; height: 2px; background: #E5E7EB; margin: 0 auto; width: 100%;">
                                <div style="position: absolute; top: 50%; left: 0; transform: translateY(-50%); width: 8px; height: 8px; background: #14B8A6; border-radius: 50%;"></div>
                                <div style="position: absolute; top: 50%; right: 0; transform: translateY(-50%); width: 0; height: 0; border-left: 8px solid #DC2626; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
                            </div>
                            <div style="color: #6B7280; font-size: 11px; margin-top: 6px;">Direct Flight</div>
                        </div>
                        
                        <div style="flex: 1; text-align: right;">
                            <div style="color: #9CA3AF; font-size: 12px; margin-bottom: 4px;">{departure_date}</div>
                            <div style="font-size: 28px; font-weight: 700; color: #1F2937; margin-bottom: 2px;">{arrival_time}</div>
                            <div style="color: #DC2626; font-size: 16px; font-weight: 600; background: #FEE2E2; padding: 4px 12px; border-radius: 6px; display: inline-block;">{arrival_airport}</div>
                        </div>
                    </div>
                </div>
        '''
        
        # Add return flight if round trip
        if is_round_trip:
            html += f'''
                <!-- Return Flight -->
                <div style="padding: 25px 20px;">
                    <div style="color: #6366F1; font-size: 13px; font-weight: 600; margin-bottom: 15px;">↩️ RETURN FLIGHT</div>
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="flex: 1;">
                            <div style="color: #9CA3AF; font-size: 12px; margin-bottom: 4px;">{return_date}</div>
                            <div style="font-size: 28px; font-weight: 700; color: #1F2937; margin-bottom: 2px;">{arrival_time}</div>
                            <div style="color: #DC2626; font-size: 16px; font-weight: 600; background: #FEE2E2; padding: 4px 12px; border-radius: 6px; display: inline-block;">{arrival_airport}</div>
                        </div>
                        
                        <div style="flex: 1; text-align: center; padding: 0 15px;">
                            <div style="color: #9CA3AF; font-size: 12px; margin-bottom: 6px;">{duration}</div>
                            <div style="position: relative; height: 2px; background: #E5E7EB; margin: 0 auto; width: 100%;">
                                <div style="position: absolute; top: 50%; left: 0; transform: translateY(-50%); width: 8px; height: 8px; background: #DC2626; border-radius: 50%;"></div>
                                <div style="position: absolute; top: 50%; right: 0; transform: translateY(-50%); width: 0; height: 0; border-left: 8px solid #14B8A6; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
                            </div>
                            <div style="color: #6B7280; font-size: 11px; margin-top: 6px;">Direct Flight</div>
                        </div>
                        
                        <div style="flex: 1; text-align: right;">
                            <div style="color: #9CA3AF; font-size: 12px; margin-bottom: 4px;">{return_date}</div>
                            <div style="font-size: 28px; font-weight: 700; color: #1F2937; margin-bottom: 2px;">{departure_time}</div>
                            <div style="color: #14B8A6; font-size: 16px; font-weight: 600; background: #F0FDFA; padding: 4px 12px; border-radius: 6px; display: inline-block;">{departure_airport}</div>
                        </div>
                    </div>
                </div>
            '''
        else:
            # Close the card if not round trip
            html += '''
            '''
        
        # Add booking info footer
        html += f'''
                <!-- Booking Info -->
                <div style="background: #F9FAFB; padding: 15px 20px; border-top: 1px solid #E5E7EB;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: #6B7280; font-size: 13px;">
                            <span style="font-weight: 600; color: #374151;">Booking ID:</span> {booking_details.get("booking_id", "N/A")}
                        </div>
                        <div style="color: #6B7280; font-size: 13px;">
                            <span style="font-weight: 600; color: #374151;">Status:</span> 
                            <span style="background: #10B981; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">CONFIRMED</span>
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
        '''
        
        return html
    
    
    def _generate_html_email(
        self,
        user_name: str,
        summary: str,
        transcript: Optional[List[Dict]] = None,
        booking_details: Optional[Dict] = None,
        call_duration: Optional[int] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """Generate HTML formatted email"""
        
        # Calculate duration - handle different formats from Vapi
        duration_text = "Not available"
        if call_duration:
            try:
                # Convert to float first (handles int, float, and numeric strings)
                duration_seconds = float(call_duration)
                
                # Convert to integer seconds
                total_seconds = int(duration_seconds)
                
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                duration_text = f"{minutes} minutes {seconds} seconds"
            except (ValueError, TypeError):
                # If conversion fails, just display as string
                duration_text = str(call_duration)
        
        # Build transcript HTML
        transcript_html = ""
        if transcript and len(transcript) > 0:
            transcript_items = []
            for msg in transcript:
                role = msg.get("role", "")
                message = msg.get("message", "")
                
                # Skip system messages - only show user and assistant conversations
                if role.lower() == "system":
                    continue
                
                role_display = role.capitalize()
                
                # Style based on role
                if role.lower() in ["user", "customer"]:
                    color = "#14B8A6"
                    bg_color = "#F0FDFA"
                else:
                    color = "#6366F1"
                    bg_color = "#EEF2FF"
                
                transcript_items.append(f"""
                    <div style="margin-bottom: 15px; padding: 15px; background-color: {bg_color}; border-left: 4px solid {color}; border-radius: 8px;">
                        <div style="font-weight: bold; color: {color}; margin-bottom: 5px;">{role_display}:</div>
                        <div style="color: #374151;">{message}</div>
                    </div>
                """)
            
            transcript_html = "".join(transcript_items)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #F9FAFB;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F9FAFB; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: #000000; padding: 40px; text-align: center;">
                                    <h1 style="margin: 0; color: #FFFFFF; font-size: 28px; font-weight: 600;">Attar Travel</h1>
                                    <p style="margin: 10px 0 0 0; color: #FFFFFF; font-size: 16px;">Your Conversation Summary</p>
                                </td>
                            </tr>
                            
                            <!-- Greeting -->
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="margin: 0 0 20px 0; font-size: 16px; color: #374151; line-height: 1.6;">
                                        Hello <strong>{user_name}</strong>,
                                    </p>
                                    <p style="margin: 0; font-size: 16px; color: #374151; line-height: 1.6;">
                                        Thank you for chatting with <strong>Attar Travel</strong>! Here's a summary of your recent conversation with our AI assistant.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Conversation Details Section -->
                            {f'''
                            <tr>
                                <td style="padding: 0 40px 40px 40px;">
                                    <div style="border-bottom: 2px solid #E5E7EB; padding-bottom: 30px; margin-bottom: 30px;">
                                        <h2 style="margin: 0 0 15px 0; color: #1F2937; font-size: 20px; font-weight: 600;">Conversation Details</h2>
                                        <div style="color: #374151; font-size: 15px; line-height: 1.8;">
                                            {f'<p style="margin: 8px 0;"><strong>Session ID:</strong> {session_id}</p>' if session_id else ''}
                                            {f'<p style="margin: 8px 0;"><strong>Total messages:</strong> {sum(1 for msg in transcript if msg.get("role", "").lower() != "system")}</p>' if transcript else ''}
                                            {f'<p style="margin: 8px 0;"><strong>Call Date:</strong> {timestamp}</p>' if timestamp else ''}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                            ''' if (session_id or timestamp or transcript) else ''}
                            
                            <!-- Summary Section -->
                            <tr>
                                <td style="padding: 0 40px 40px 40px;">
                                    <div style="border-bottom: 2px solid #E5E7EB; padding-bottom: 30px; margin-bottom: 30px;">
                                        <h2 style="margin: 0 0 20px 0; color: #1F2937; font-size: 20px; font-weight: 600;">Conversation Summary</h2>
                                        <div style="color: #374151; font-size: 15px; line-height: 1.8;">
                                            {self._format_summary_html(summary)}
                                        </div>
                                    </div>
                                    
                                    <!-- Duration -->
                                    <div style="border-bottom: 2px solid #E5E7EB; padding-bottom: 30px; margin-bottom: 30px;">
                                        <h2 style="margin: 0 0 10px 0; color: #1F2937; font-size: 18px; font-weight: 600;">Call Duration</h2>
                                        <p style="margin: 0; color: #374151; font-size: 15px;">{duration_text}</p>
                                    </div>
                                    
                                    <!-- Booking Details Card -->
                                    {self._generate_booking_card_html(booking_details) if booking_details else ''}
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #F9FAFB; padding: 30px 40px; text-align: center; border-top: 1px solid #E5E7EB;">
                                    <p style="margin: 0 0 10px 0; color: #6B7280; font-size: 14px;">
                                        Best regards,<br>
                                        <strong style="color: #374151;">Attar Travel Team</strong>
                                    </p>
                                    <p style="margin: 0; color: #6B7280; font-size: 14px;">
                                        <strong>Attar Travels</strong><br>
                                        <a href="mailto:attartravel25@gmail.com" style="color: #14B8A6; text-decoration: none;">attartravel25@gmail.com</a>
                                    </p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return html


# Create global instance
smtp_email_service = SMTPEmailService()

