from django.utils import timezone
from datetime import timedelta
from .models import Booking, ParkingSlot


class OverbookingPreventionSystem:
    
    @staticmethod
    def check_slot_conflicts(slot, start_time, end_time, exclude_booking_id=None):
        overlapping_bookings = Booking.objects.filter(
            slot=slot,
            status__in=['reserved', 'confirmed', 'active'],
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if exclude_booking_id:
            overlapping_bookings = overlapping_bookings.exclude(id=exclude_booking_id)
        
        return overlapping_bookings.exists()
    
    @staticmethod
    def get_slot_availability_window(slot, duration_hours=1):
        now = timezone.now()
        
        conflicting_bookings = Booking.objects.filter(
            slot=slot,
            status__in=['reserved', 'confirmed', 'active'],
            start_time__gte=now
        ).order_by('start_time')
        
        available_windows = []
        
        if not conflicting_bookings.exists():
            available_windows.append({
                'start': now,
                'end': now + timedelta(hours=24),
                'duration_minutes': 24 * 60
            })
        else:
            current_time = now
            
            for booking in conflicting_bookings:
                if current_time < booking.start_time:
                    gap_minutes = int((booking.start_time - current_time).total_seconds() / 60)
                    if gap_minutes >= (duration_hours * 60):
                        available_windows.append({
                            'start': current_time,
                            'end': booking.start_time,
                            'duration_minutes': gap_minutes
                        })
                
                current_time = max(current_time, booking.end_time)
            
            if current_time < now + timedelta(hours=24):
                gap_minutes = int((now + timedelta(hours=24) - current_time).total_seconds() / 60)
                if gap_minutes >= (duration_hours * 60):
                    available_windows.append({
                        'start': current_time,
                        'end': now + timedelta(hours=24),
                        'duration_minutes': gap_minutes
                    })
        
        return available_windows
    
    @staticmethod
    def get_peak_hours():
        return {
            'monday': [(9, 11), (12, 14), (17, 19)],
            'tuesday': [(9, 11), (12, 14), (17, 19)],
            'wednesday': [(9, 11), (12, 14), (17, 19)],
            'thursday': [(9, 11), (12, 14), (17, 19)],
            'friday': [(9, 11), (12, 14), (17, 19), (20, 23)],
            'saturday': [(10, 12), (14, 16), (18, 21)],
            'sunday': [(10, 12), (14, 16), (18, 20)],
        }
    
    @staticmethod
    def check_capacity_threshold(threshold=0.8):
        total_slots = ParkingSlot.objects.count()
        if total_slots == 0:
            return False
        
        occupied_slots = ParkingSlot.objects.filter(is_occupied=True).count()
        occupancy_rate = occupied_slots / total_slots
        
        return occupancy_rate >= threshold
    
    @staticmethod
    def get_overbooking_alerts():
        alerts = []
        
        total_slots = ParkingSlot.objects.count()
        occupied_slots = ParkingSlot.objects.filter(is_occupied=True).count()
        occupancy_rate = occupied_slots / max(1, total_slots)
        
        if occupancy_rate >= 0.9:
            alerts.append({
                'level': 'critical',
                'message': f'Critical: Occupancy at {occupancy_rate*100:.1f}%',
                'occupied': occupied_slots,
                'total': total_slots
            })
        elif occupancy_rate >= 0.8:
            alerts.append({
                'level': 'warning',
                'message': f'Warning: Occupancy at {occupancy_rate*100:.1f}%',
                'occupied': occupied_slots,
                'total': total_slots
            })
        
        expiring_bookings = Booking.objects.filter(
            status='reserved',
            expires_at__lt=timezone.now() + timedelta(minutes=5),
            expires_at__gt=timezone.now()
        )
        
        if expiring_bookings.count() > 0:
            alerts.append({
                'level': 'info',
                'message': f'{expiring_bookings.count()} bookings expiring soon',
                'count': expiring_bookings.count()
            })
        
        expired_bookings = Booking.objects.filter(
            status='reserved',
            expires_at__lt=timezone.now()
        )
        
        for booking in expired_bookings:
            booking.status = 'expired'
            booking.slot.is_occupied = False
            booking.save()
            booking.slot.save()
        
        if expired_bookings.count() > 0:
            alerts.append({
                'level': 'warning',
                'message': f'{expired_bookings.count()} bookings expired and released',
                'count': expired_bookings.count()
            })
        
        return alerts
    
    @staticmethod
    def get_booking_statistics():
        now = timezone.now()
        
        total_bookings = Booking.objects.count()
        active_bookings = Booking.objects.filter(status='active').count()
        confirmed_bookings = Booking.objects.filter(status='confirmed').count()
        completed_bookings = Booking.objects.filter(status='completed').count()
        
        bookings_today = Booking.objects.filter(
            created_at__date=now.date()
        ).count()
        
        peak_slot_count = Booking.objects.filter(
            status__in=['reserved', 'confirmed', 'active'],
            start_time__lte=now,
            end_time__gt=now
        ).count()
        
        return {
            'total': total_bookings,
            'active': active_bookings,
            'confirmed': confirmed_bookings,
            'completed': completed_bookings,
            'today': bookings_today,
            'current_occupancy': peak_slot_count
        }


def release_expired_reservations():
    now = timezone.now()
    expired_bookings = Booking.objects.filter(
        status='reserved',
        expires_at__lt=now
    )
    
    for booking in expired_bookings:
        booking.status = 'expired'
        booking.slot.is_occupied = False
        booking.slot.save()
        booking.save()
        
        try:
            from .email_notifications import send_booking_expiration_alert
            send_booking_expiration_alert(booking)
        except Exception as e:
            print(f"Error sending expiration alert: {e}")
        
        try:
            from .sms_notifications import send_booking_expiration_sms
            send_booking_expiration_sms(booking)
        except Exception as e:
            print(f"Error sending expiration SMS: {e}")
    
    return expired_bookings.count()
