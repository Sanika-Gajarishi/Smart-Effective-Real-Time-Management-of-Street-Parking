import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from parking_app.models import ParkingSlot, Reservation, Booking, Transaction


class ParkingNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.user_id = str(self.user.id)
            await self.channel_layer.group_add(
                f"user_{self.user_id}",
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f"user_{self.user_id}",
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'get_slot_status':
            slot_id = data.get('slot_id')
            slot_status = await self.get_slot_status(slot_id)
            await self.send(text_data=json.dumps({
                'type': 'slot_status',
                'data': slot_status
            }))

    async def slot_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'slot_update',
            'data': event['data']
        }))

    async def reservation_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reservation_notification',
            'title': event['title'],
            'message': event['message'],
            'reservation_id': event.get('reservation_id')
        }))

    async def booking_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'booking_status_update',
            'booking_id': event['booking_id'],
            'status': event['status'],
            'message': event['message'],
            'timestamp': event.get('timestamp')
        }))

    async def transaction_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'transaction_status_update',
            'transaction_id': event['transaction_id'],
            'status': event['status'],
            'amount': str(event['amount']),
            'gateway': event['gateway'],
            'message': event['message'],
            'timestamp': event.get('timestamp')
        }))

    async def real_time_slot_availability(self, event):
        await self.send(text_data=json.dumps({
            'type': 'real_time_slot_availability',
            'slot_id': event['slot_id'],
            'occupied': event['occupied'],
            'available_count': event['available_count'],
            'total_count': event['total_count'],
            'occupancy_rate': event['occupancy_rate']
        }))

    @database_sync_to_async
    def get_slot_status(self, slot_id):
        try:
            slot = ParkingSlot.objects.get(id=slot_id)
            return {
                'id': slot.id,
                'slot_number': slot.slot_number,
                'is_occupied': slot.is_occupied,
                'latitude': slot.latitude,
                'longitude': slot.longitude
            }
        except ParkingSlot.DoesNotExist:
            return None
