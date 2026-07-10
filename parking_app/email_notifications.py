from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_reservation_confirmation(reservation):
    subject = f'🅿️ Parking Slot Reserved - Slot #{reservation.slot_number}'
    
    context = {
        'user': reservation.user.first_name or reservation.user.username,
        'slot_number': reservation.slot_number,
        'vehicle_number': reservation.vehicle_number,
        'vehicle_type': reservation.vehicle_type,
        'start_time': reservation.start_time,
        'end_time': reservation.end_time,
        'reservation_id': reservation.id,
    }
    
    html_message = render_to_string('emails/reservation_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_payment_confirmation(reservation, amount):
    subject = f'✅ Payment Confirmed - Reservation #{reservation.id}'
    
    context = {
        'user': reservation.user.first_name or reservation.user.username,
        'reservation_id': reservation.id,
        'amount': amount,
        'slot_number': reservation.slot_number,
        'vehicle_number': reservation.vehicle_number,
    }
    
    html_message = render_to_string('emails/payment_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_over_parking_alert(reservation, over_parking_minutes):
    subject = f'⚠️ Over-Parking Alert - Reservation #{reservation.id}'
    
    context = {
        'user': reservation.user.first_name or reservation.user.username,
        'reservation_id': reservation.id,
        'slot_number': reservation.slot_number,
        'vehicle_number': reservation.vehicle_number,
        'over_parking_minutes': over_parking_minutes,
    }
    
    html_message = render_to_string('emails/over_parking_alert.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_over_parking_alert_email(reservation, additional_charge):
    subject = f'⚠️ Over-Parking Charge - Reservation #{reservation.id}'
    
    context = {
        'user': reservation.user.first_name or reservation.user.username,
        'reservation_id': reservation.id,
        'slot_number': reservation.slot_number,
        'vehicle_number': reservation.vehicle_number,
        'additional_charge': additional_charge,
    }
    
    html_message = render_to_string('emails/over_parking_alert.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_check_in_confirmation(reservation):
    subject = f'✓ Check-In Confirmed - Slot #{reservation.slot_number}'
    
    context = {
        'user': reservation.user.first_name or reservation.user.username,
        'reservation_id': reservation.id,
        'slot_number': reservation.slot_number,
        'vehicle_number': reservation.vehicle_number,
        'check_in_time': reservation.checked_in_at,
    }
    
    html_message = render_to_string('emails/check_in_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_check_out_receipt(reservation):
    subject = f'🎟️ Parking Receipt - Reservation #{reservation.id}'
    
    total_amount = reservation.amount + reservation.over_parking_charges
    
    context = {
        'user': reservation.user.first_name or reservation.user.username,
        'reservation_id': reservation.id,
        'slot_number': reservation.slot_number,
        'vehicle_number': reservation.vehicle_number,
        'start_time': reservation.start_time,
        'actual_checkout_time': reservation.actual_checkout_time,
        'parking_amount': reservation.amount,
        'over_parking_charges': reservation.over_parking_charges,
        'total_amount': total_amount,
    }
    
    html_message = render_to_string('emails/checkout_receipt.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_booking_reserved_alert(booking):
    subject = f'🅿️ Parking Slot Reserved Temporarily - Slot #{booking.slot.slot_number}'
    
    context = {
        'user': booking.user.first_name or booking.user.username,
        'booking_id': booking.id,
        'slot_number': booking.slot.slot_number,
        'vehicle_number': booking.vehicle_number,
        'vehicle_type': booking.vehicle_type,
        'start_time': booking.start_time,
        'end_time': booking.end_time,
        'amount': booking.base_amount,
        'expires_at': booking.expires_at,
    }
    
    html_message = render_to_string('emails/booking_reserved.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_booking_confirmed_alert(booking):
    subject = f'✅ Booking Confirmed - Slot #{booking.slot.slot_number}'
    
    context = {
        'user': booking.user.first_name or booking.user.username,
        'booking_id': booking.id,
        'slot_number': booking.slot.slot_number,
        'vehicle_number': booking.vehicle_number,
        'vehicle_type': booking.vehicle_type,
        'start_time': booking.start_time,
        'end_time': booking.end_time,
        'amount': booking.base_amount,
        'confirmed_at': booking.confirmed_at,
    }
    
    html_message = render_to_string('emails/booking_confirmed.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_transaction_initiated_alert(transaction):
    subject = f'💳 Payment Initiated - Booking #{transaction.booking.id}'
    
    context = {
        'user': transaction.user.first_name or transaction.user.username,
        'transaction_id': transaction.id,
        'booking_id': transaction.booking.id,
        'amount': transaction.amount,
        'gateway': transaction.gateway.upper(),
        'slot_number': transaction.booking.slot.slot_number,
    }
    
    html_message = render_to_string('emails/transaction_initiated.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [transaction.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_transaction_success_alert(transaction):
    subject = f'✅ Payment Successful - Booking #{transaction.booking.id}'
    
    context = {
        'user': transaction.user.first_name or transaction.user.username,
        'transaction_id': transaction.id,
        'booking_id': transaction.booking.id,
        'amount': transaction.amount,
        'gateway': transaction.gateway.upper(),
        'slot_number': transaction.booking.slot.slot_number,
        'completed_at': transaction.completed_at,
    }
    
    html_message = render_to_string('emails/transaction_success.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [transaction.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_transaction_failed_alert(transaction):
    subject = f'❌ Payment Failed - Booking #{transaction.booking.id}'
    
    context = {
        'user': transaction.user.first_name or transaction.user.username,
        'transaction_id': transaction.id,
        'booking_id': transaction.booking.id,
        'amount': transaction.amount,
        'gateway': transaction.gateway.upper(),
        'error_message': transaction.error_message,
    }
    
    html_message = render_to_string('emails/transaction_failed.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [transaction.user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_booking_expiration_alert(booking):
    subject = f'⏰ Booking Expired - Reservation #{booking.id}'
    
    context = {
        'user': booking.user.first_name or booking.user.username,
        'booking_id': booking.id,
        'slot_number': booking.slot.slot_number,
        'vehicle_number': booking.vehicle_number,
    }
    
    html_message = render_to_string('emails/booking_expired.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        html_message=html_message,
        fail_silently=True,
    )
