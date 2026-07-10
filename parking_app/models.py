
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import secrets

# Existing Profile and Reservation
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    wallet_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    verified_2fa = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"

class Reservation(models.Model):
    PAYMENT_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
        ('Active', 'Active'),
        ('Checked-In', 'Checked-In'),
        ('Over-Parked', 'Over-Parked'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slot_number = models.CharField(max_length=10)
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=20, default='car')
    reservation_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    actual_checkout_time = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    over_parking_charges = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='Pending')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    is_over_parked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Slot {self.slot_number}"
    
    def calculate_over_parking_charges(self):
        if self.actual_checkout_time and self.end_time:
            overparked_hours = (self.actual_checkout_time - self.end_time).total_seconds() / 3600
            if overparked_hours > 0:
                base_rate = 50
                congestion_factor = 1.5
                self.over_parking_charges = round(overparked_hours * base_rate * congestion_factor, 2)
                self.is_over_parked = True
                return self.over_parking_charges
        return 0.00
    
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

# New Models for Parking
class ParkingLot(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    total_slots = models.IntegerField()
    
    def __str__(self):
        return self.name

class ParkingSlot(models.Model):
    VEHICLE_TYPES = [
        ('bike', 'Bike'),
        ('car', 'Car'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('ev', 'EV'),
    ]
    
    SLOT_TYPES = [
        ('Open', 'Open'),
        ('Reserved', 'Reserved'),
        ('EV', 'EV'),
    ]
    
    BOOKING_STATUSES = [
        ('Available', 'Available'),
        ('Booked', 'Booked'),
    ]

    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    slot_number = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_occupied = models.BooleanField(default=False)

    allowed_vehicle_types = models.JSONField(default=list)
    has_ev_charger = models.BooleanField(default=False)
    
    preferred_slot_type = models.CharField(max_length=20, choices=SLOT_TYPES, default='Open')
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUSES, default='Available')

    def __str__(self):
        return f"{self.lot.name} - Slot {self.slot_number}"


class ParkingMonitor(models.Model):
    MONITORING_STATUS = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Alert-Over-Parking', 'Alert-Over-Parking'),
        ('Cancelled', 'Cancelled'),
    ]
    
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='monitor')
    start_monitoring = models.DateTimeField(auto_now_add=True)
    last_check = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=MONITORING_STATUS, default='Active')
    over_parking_detected = models.BooleanField(default=False)
    over_parking_duration_minutes = models.IntegerField(default=0)
    security_alert_sent = models.BooleanField(default=False)
    over_parking_charged = models.BooleanField(default=False)
    over_parking_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Monitor - {self.reservation.vehicle_number}"

class AdypuUser(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=10)
    vehicle_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user_id} - {self.name}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reservation', 'Reservation'),
        ('payment', 'Payment'),
        ('check_in', 'Check-In'),
        ('check_out', 'Check-Out'),
        ('over_parking', 'Over-Parking'),
        ('alert', 'Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField(unique=True)
    device_type = models.CharField(max_length=20, choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reserved', 'Reserved (Temp)'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='bookings')
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    reserved_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    check_in_qr = models.TextField(blank=True, null=True)
    check_out_qr = models.TextField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False, help_text='Whether SMS reminder has been sent')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} - Slot {self.slot.slot_number}"


class Transaction(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('wallet', 'Wallet'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='transaction')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='initiated')
    
    gateway_order_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_payment_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_signature = models.CharField(max_length=255, blank=True, null=True)
    
    error_message = models.TextField(blank=True, null=True)
    
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-initiated_at']
    
    def __str__(self):
        return f"Transaction #{self.id} - Booking #{self.booking.id} - {self.status}"


class Refund(models.Model):
    REFUND_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='refund')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refunds')
    
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='initiated')
    reason = models.TextField()
    
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    gateway_refund_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-initiated_at']
    
    def __str__(self):
        return f"Refund #{self.id} - Booking #{self.booking.id} - ₹{self.refund_amount}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    gateway_order_id = models.CharField(max_length=255)
    gateway_payment_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment #{self.id} - {self.gateway} - {self.status}"


class ETicket(models.Model):
    TICKET_STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('used', 'Used'),
        ('invalid', 'Invalid'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='e_tickets')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='e_ticket')
    ticket_number = models.CharField(max_length=20, unique=True)
    qr_code = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=TICKET_STATUS_CHOICES, default='valid')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"ETicket #{self.ticket_number} - {self.user.username} - {self.status}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.booking.end_time
    
    def get_status_display(self):
        if self.status == 'valid':
            if self.is_expired():
                return 'expired'
        return self.status
