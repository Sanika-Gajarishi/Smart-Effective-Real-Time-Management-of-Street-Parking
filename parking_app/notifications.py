from .models import Notification


def create_reservation_notification(user, reservation):
    Notification.objects.create(
        user=user,
        notification_type='reservation',
        title='🅿️ Parking Slot Reserved',
        message=f'Your parking slot #{reservation.slot_number} has been reserved. Proceed to payment.',
        reservation=reservation,
    )


def create_payment_notification(user, reservation, amount):
    Notification.objects.create(
        user=user,
        notification_type='payment',
        title='✅ Payment Successful',
        message=f'Payment of ₹{amount} for slot #{reservation.slot_number} completed successfully.',
        reservation=reservation,
    )


def create_check_in_notification(user, reservation):
    Notification.objects.create(
        user=user,
        notification_type='check_in',
        title='✓ Check-In Confirmed',
        message=f'You have successfully checked in to slot #{reservation.slot_number}.',
        reservation=reservation,
    )


def create_check_out_notification(user, reservation, amount):
    Notification.objects.create(
        user=user,
        notification_type='check_out',
        title='🎟️ Check-Out Complete',
        message=f'Your parking session ended. Total charge: ₹{amount}. Receipt sent to email.',
        reservation=reservation,
    )


def create_over_parking_notification(user, reservation, minutes):
    Notification.objects.create(
        user=user,
        notification_type='over_parking',
        title='⚠️ Over-Parking Alert',
        message=f'Your parking for slot #{reservation.slot_number} has exceeded time limit by {minutes} minutes.',
        reservation=reservation,
    )


def create_alert_notification(user, title, message, reservation=None):
    Notification.objects.create(
        user=user,
        notification_type='alert',
        title=title,
        message=message,
        reservation=reservation,
    )
