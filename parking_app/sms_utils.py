from twilio.rest import Client
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Booking
import logging

logger = logging.getLogger(__name__)

def send_sms(to_phone, message):
    """
    Send SMS using Twilio
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.error("Twilio credentials not configured")
        return False
    
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        logger.info(f"SMS sent to {to_phone}: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
        return False

def send_booking_reminder(booking_id):
    """
    Send reminder SMS for a booking 10 minutes before it ends
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        if not booking.user.profile.phone:
            logger.warning(f"No phone number found for user {booking.user.username}")
            return False
            
        message = (
            f"🔔 Parking Reminder: Your parking at slot {booking.slot.slot_number} "
            f"will expire at {booking.end_time.strftime('%I:%M %p')}. "
            f"Please extend your parking if needed. Thank you!"
        )
        
        return send_sms(booking.user.profile.phone, message)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
    except Exception as e:
        logger.error(f"Error sending booking reminder: {str(e)}")
    
    return False
