from django.contrib import admin
from .models import Profile, Reservation, ParkingLot, ParkingSlot, ParkingMonitor, AdypuUser, Notification, DeviceToken, Payment, Booking, Transaction, ETicket, Refund

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'wallet_inr', 'two_factor_enabled')
    search_fields = ('user__username', 'phone')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_number', 'slot_number', 'status', 'payment_status', 'is_over_parked')
    list_filter = ('status', 'payment_status', 'is_over_parked', 'created_at')
    search_fields = ('user__username', 'vehicle_number', 'slot_number')
    readonly_fields = ('created_at',)

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'total_slots')
    search_fields = ('name',)

@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('lot', 'slot_number', 'is_occupied', 'has_ev_charger')
    list_filter = ('lot', 'is_occupied', 'has_ev_charger')
    search_fields = ('slot_number', 'lot__name')

@admin.register(ParkingMonitor)
class ParkingMonitorAdmin(admin.ModelAdmin):
    list_display = ('get_vehicle_number', 'status', 'over_parking_detected', 'over_parking_duration_minutes')
    list_filter = ('status', 'over_parking_detected', 'start_monitoring')
    search_fields = ('reservation__vehicle_number',)
    readonly_fields = ('start_monitoring',)
    
    def get_vehicle_number(self, obj):
        return obj.reservation.vehicle_number
    get_vehicle_number.short_description = 'Vehicle Number'

@admin.register(AdypuUser)
class AdypuUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'role', 'vehicle_type', 'vehicle_number')
    list_filter = ('role', 'vehicle_type')
    search_fields = ('user_id', 'name', 'vehicle_number')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'token')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'gateway', 'status', 'created_at')
    list_filter = ('gateway', 'status', 'created_at')
    search_fields = ('user__username', 'gateway_order_id', 'gateway_payment_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vehicle_number', 'status', 'start_time', 'end_time')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'vehicle_number')
    readonly_fields = ('created_at',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'gateway', 'status', 'initiated_at')
    list_filter = ('gateway', 'status', 'initiated_at')
    search_fields = ('user__username', 'gateway_order_id', 'gateway_payment_id')
    readonly_fields = ('initiated_at', 'updated_at')

@admin.register(ETicket)
class ETicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'status', 'generated_at')
    list_filter = ('status', 'generated_at')
    search_fields = ('ticket_number', 'user__username')
    readonly_fields = ('generated_at',)

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'refund_amount', 'status', 'initiated_at')
    list_filter = ('status', 'initiated_at')
    search_fields = ('user__username',)
    readonly_fields = ('initiated_at',)
