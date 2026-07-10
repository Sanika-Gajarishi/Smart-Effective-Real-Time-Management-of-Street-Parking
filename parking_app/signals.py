from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False

from .models import Booking, Transaction, ParkingSlot


@receiver(post_save, sender=Booking)
def broadcast_booking_status_update(sender, instance, created, **kwargs):
    if not CHANNELS_AVAILABLE:
        return
    
    try:
        channel_layer = get_channel_layer()
        user_id = str(instance.user.id)
        
        message = {
            'type': 'booking_status_update',
            'booking_id': instance.id,
            'status': instance.status,
            'message': f'Booking #{instance.id} status: {instance.get_status_display()}',
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            message
        )
    except Exception as e:
        print(f"Error broadcasting booking status: {e}")


@receiver(post_save, sender=Transaction)
def broadcast_transaction_status_update(sender, instance, created, **kwargs):
    if not CHANNELS_AVAILABLE:
        return
    
    try:
        channel_layer = get_channel_layer()
        user_id = str(instance.user.id)
        
        message = {
            'type': 'transaction_status_update',
            'transaction_id': instance.id,
            'status': instance.status,
            'amount': str(instance.amount),
            'gateway': instance.gateway,
            'message': f'Payment via {instance.gateway.upper()} - {instance.get_status_display()}',
            'timestamp': timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            message
        )
    except Exception as e:
        print(f"Error broadcasting transaction status: {e}")


@receiver(post_save, sender=ParkingSlot)
def broadcast_slot_availability_update(sender, instance, **kwargs):
    if not CHANNELS_AVAILABLE:
        return
    
    try:
        channel_layer = get_channel_layer()
        
        total_slots = ParkingSlot.objects.count()
        occupied_slots = ParkingSlot.objects.filter(is_occupied=True).count()
        available_slots = total_slots - occupied_slots
        occupancy_rate = round((occupied_slots / max(1, total_slots)) * 100, 2)
        
        message = {
            'type': 'real_time_slot_availability',
            'slot_id': instance.id,
            'occupied': instance.is_occupied,
            'available_count': available_slots,
            'total_count': total_slots,
            'occupancy_rate': occupancy_rate
        }
        
        async_to_sync(channel_layer.group_send)(
            "parking_updates",
            message
        )
    except Exception as e:
        print(f"Error broadcasting slot availability: {e}")
