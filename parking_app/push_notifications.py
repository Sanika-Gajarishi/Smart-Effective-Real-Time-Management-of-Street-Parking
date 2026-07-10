import json
import requests
from django.conf import settings


def send_firebase_notification(device_token, title, body, data=None):
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={settings.FIREBASE_API_KEY}"
        }
        
        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
            },
            "data": data or {}
        }
        
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return None


def send_reservation_push(user, reservation):
    from parking_app.models import DeviceToken
    
    try:
        device_tokens = DeviceToken.objects.filter(user=user, is_active=True)
        for token in device_tokens:
            send_firebase_notification(
                device_token=token.token,
                title="🅿️ Parking Slot Reserved",
                body=f"Your slot #{reservation.slot_number} is reserved.",
                data={
                    'reservation_id': str(reservation.id),
                    'slot_number': str(reservation.slot_number),
                    'action': 'reservation'
                }
            )
    except Exception as e:
        print(f"Error sending reservation push: {e}")


def send_check_in_push(user, reservation):
    from parking_app.models import DeviceToken
    
    try:
        device_tokens = DeviceToken.objects.filter(user=user, is_active=True)
        for token in device_tokens:
            send_firebase_notification(
                device_token=token.token,
                title="✓ Check-In Confirmed",
                body=f"You've checked in to slot #{reservation.slot_number}.",
                data={
                    'reservation_id': str(reservation.id),
                    'action': 'check_in'
                }
            )
    except Exception as e:
        print(f"Error sending check-in push: {e}")


def send_check_out_push(user, reservation, total_charge):
    from parking_app.models import DeviceToken
    
    try:
        device_tokens = DeviceToken.objects.filter(user=user, is_active=True)
        for token in device_tokens:
            send_firebase_notification(
                device_token=token.token,
                title="🎟️ Check-Out Complete",
                body=f"Total charge: ₹{total_charge}. Receipt sent to email.",
                data={
                    'reservation_id': str(reservation.id),
                    'total_charge': str(total_charge),
                    'action': 'check_out'
                }
            )
    except Exception as e:
        print(f"Error sending check-out push: {e}")


def send_over_parking_push(user, reservation, additional_charge):
    from parking_app.models import DeviceToken
    
    try:
        device_tokens = DeviceToken.objects.filter(user=user, is_active=True)
        for token in device_tokens:
            send_firebase_notification(
                device_token=token.token,
                title="⚠️ Over-Parking Alert",
                body=f"Additional charge: ₹{additional_charge}. Please check-out soon.",
                data={
                    'reservation_id': str(reservation.id),
                    'additional_charge': str(additional_charge),
                    'action': 'over_parking'
                }
            )
    except Exception as e:
        print(f"Error sending over-parking push: {e}")
