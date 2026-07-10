from twilio.rest import Client
from django.conf import settings
from django.db import models


def send_sms(phone_number, message):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return message.sid
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None


def send_reservation_sms(reservation):
    phone_number = reservation.user.profile.phone
    message = f"🅿️ Your parking slot #{reservation.slot_number} is reserved. Total: ₹{reservation.calculated_price()}. Duration: 2 hours."
    return send_sms(phone_number, message)


def send_check_in_sms(reservation):
    phone_number = reservation.user.profile.phone
    message = f"✓ Check-in successful! Slot #{reservation.slot_number}. Session started at {reservation.start_time.strftime('%H:%M')}"
    return send_sms(phone_number, message)


def send_check_out_sms(reservation, total_charge):
    phone_number = reservation.user.profile.phone
    message = f"🎟️ Check-out complete! Slot #{reservation.slot_number}. Total charge: ₹{total_charge}. Receipt sent to email."
    return send_sms(phone_number, message)


def send_over_parking_alert(reservation, additional_charge):
    phone_number = reservation.user.profile.phone
    message = f"⚠️ Over-parking alert! Slot #{reservation.slot_number}. Additional charge: ₹{additional_charge}. Please check-out soon."
    return send_sms(phone_number, message)


def send_parking_expiry_reminder(reservation, minutes_remaining):
    phone_number = reservation.user.profile.phone
    message = f"⏰ Parking expiring soon! Slot #{reservation.slot_number}. {minutes_remaining} minutes remaining. Check-out or extend now."
    return send_sms(phone_number, message)


def send_parking_10min_alert(reservation):
    phone_number = reservation.user.profile.phone
    message = f"⏰ SMS ALERT: Your parking slot #{reservation.slot_number} expires in 10 minutes. Vehicle: {reservation.vehicle_number}. Please proceed to checkout immediately."
    return send_sms(phone_number, message)


def send_booking_reserved_sms(booking):
    phone_number = booking.user.profile.phone
    message = f"🅿️ Slot #{booking.slot.slot_number} reserved! Amount: ₹{booking.base_amount}. Complete payment within 15 minutes."
    return send_sms(phone_number, message)


def send_booking_confirmed_sms(booking):
    phone_number = booking.user.profile.phone
    message = f"✅ Booking confirmed! Slot #{booking.slot.slot_number}. {booking.vehicle_number}. Duration: {(booking.end_time - booking.start_time).total_seconds() / 3600:.1f} hours."
    return send_sms(phone_number, message)


def send_transaction_initiated_sms(transaction):
    phone_number = transaction.user.profile.phone
    message = f"💳 Payment initiated via {transaction.gateway.upper()}. Amount: ₹{transaction.amount}. Booking #{transaction.booking.id}."
    return send_sms(phone_number, message)


def send_transaction_success_sms(transaction):
    phone_number = transaction.user.profile.phone
    message = f"✅ Payment successful! ₹{transaction.amount} via {transaction.gateway.upper()}. Slot #{transaction.booking.slot.slot_number} confirmed."
    return send_sms(phone_number, message)


def send_transaction_failed_sms(transaction):
    phone_number = transaction.user.profile.phone
    message = f"❌ Payment failed! ₹{transaction.amount} via {transaction.gateway.upper()}. Reason: {transaction.error_message[:30] if transaction.error_message else 'Unknown'}. Retry booking."
    return send_sms(phone_number, message)


def send_booking_expiration_sms(booking):
    phone_number = booking.user.profile.phone
    message = f"⏰ Booking expired! Slot #{booking.slot.slot_number} released. Payment not received within 15 minutes."
    return send_sms(phone_number, message)


def send_cancellation_confirmation_sms(booking, refund_amount):
    phone_number = booking.user.profile.phone
    message = f"↩️ Booking cancelled! Slot #{booking.slot.slot_number}. Refund: ₹{refund_amount} will be processed."
    return send_sms(phone_number, message)
