# parking_app/utils_slots.py

from .models import ParkingSlot
from django.db.models import F
import random


def get_best_available_slot(vehicle_type="car"):
    """
    Returns a random available parking slot
    """

    available_slots = list(
        ParkingSlot.objects
        .filter(is_occupied=False)
        .values_list('id', flat=True)
    )

    if available_slots:
        slot_id = random.choice(available_slots)
        return ParkingSlot.objects.get(id=slot_id)

    return None
