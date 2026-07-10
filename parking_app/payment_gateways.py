import razorpay
import requests
import json
from django.conf import settings
from django.utils import timezone
from parking_app.models import Payment, Transaction


class RazorpayPaymentGateway:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    def create_order(self, reservation, amount):
        try:
            amount_in_paise = int(amount * 100)
            
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f"reservation_{reservation.id}",
                'notes': {
                    'reservation_id': str(reservation.id),
                    'slot_number': str(reservation.slot_number),
                    'vehicle_number': reservation.vehicle_number,
                }
            }
            
            order = self.client.order.create(data=order_data)
            
            Payment.objects.create(
                user=reservation.user,
                reservation=reservation,
                gateway='razorpay',
                amount=amount,
                gateway_order_id=order['id'],
                status='pending'
            )
            
            return order
        except Exception as e:
            print(f"Error creating Razorpay order: {e}")
            return None

    def create_transaction_order(self, transaction):
        try:
            amount_in_paise = int(transaction.amount * 100)
            
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f"transaction_{transaction.id}",
                'notes': {
                    'transaction_id': str(transaction.id),
                    'booking_id': str(transaction.booking.id),
                    'slot_number': str(transaction.booking.slot.slot_number),
                    'vehicle_number': transaction.booking.vehicle_number,
                }
            }
            
            order = self.client.order.create(data=order_data)
            return order
        except Exception as e:
            print(f"Error creating Razorpay order for transaction: {e}")
            return None

    def verify_payment(self, order_id, payment_id, signature):
        try:
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
        except Exception as e:
            print(f"Error verifying Razorpay payment: {e}")
            return False

    def capture_payment(self, payment_id, amount):
        try:
            amount_in_paise = int(amount * 100)
            capture = self.client.payment.capture(payment_id, amount_in_paise)
            return capture
        except Exception as e:
            print(f"Error capturing Razorpay payment: {e}")
            return None


class PayPalPaymentGateway:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.mode = settings.PAYPAL_MODE
        self.api_url = "https://api.sandbox.paypal.com" if self.mode == 'sandbox' else "https://api.paypal.com"

    def get_access_token(self):
        try:
            auth = (self.client_id, self.client_secret)
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            data = {'grant_type': 'client_credentials'}
            
            response = requests.post(
                f"{self.api_url}/v1/oauth2/token",
                auth=auth,
                headers=headers,
                data=data
            )
            
            return response.json().get('access_token')
        except Exception as e:
            print(f"Error getting PayPal access token: {e}")
            return None

    def create_order(self, reservation, amount):
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            payload = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'reference_id': f"reservation_{reservation.id}",
                    'amount': {
                        'currency_code': 'INR',
                        'value': str(amount)
                    },
                    'description': f"Parking Slot #{reservation.slot_number}",
                    'custom_id': str(reservation.id)
                }],
                'application_context': {
                    'brand_name': 'Smart Parking System',
                    'locale': 'en-US',
                    'user_action': 'PAY_NOW'
                }
            }
            
            response = requests.post(
                f"{self.api_url}/v2/checkout/orders",
                headers=headers,
                json=payload
            )
            
            order = response.json()
            
            Payment.objects.create(
                user=reservation.user,
                reservation=reservation,
                gateway='paypal',
                amount=amount,
                gateway_order_id=order['id'],
                status='pending'
            )
            
            return order
        except Exception as e:
            print(f"Error creating PayPal order: {e}")
            return None

    def create_transaction_order(self, transaction):
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            payload = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'reference_id': f"transaction_{transaction.id}",
                    'amount': {
                        'currency_code': 'INR',
                        'value': str(transaction.amount)
                    },
                    'description': f"Parking Slot #{transaction.booking.slot.slot_number}",
                    'custom_id': str(transaction.id)
                }],
                'application_context': {
                    'brand_name': 'Smart Parking System',
                    'locale': 'en-US',
                    'user_action': 'PAY_NOW'
                }
            }
            
            response = requests.post(
                f"{self.api_url}/v2/checkout/orders",
                headers=headers,
                json=payload
            )
            
            order = response.json()
            return order
        except Exception as e:
            print(f"Error creating PayPal order for transaction: {e}")
            return None

    def capture_order(self, order_id):
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.post(
                f"{self.api_url}/v2/checkout/orders/{order_id}/capture",
                headers=headers
            )
            
            return response.json()
        except Exception as e:
            print(f"Error capturing PayPal order: {e}")
            return None
