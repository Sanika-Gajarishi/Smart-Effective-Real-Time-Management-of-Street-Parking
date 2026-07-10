import csv
import os
from django.conf import settings
from collections import defaultdict

PARKING_DATA_CACHE = None

def load_parking_data():
    global PARKING_DATA_CACHE
    
    if PARKING_DATA_CACHE is not None:
        return PARKING_DATA_CACHE
    
    csv_path = os.path.join(settings.BASE_DIR, 'data', 'adypu_parking_users.csv')
    
    if not os.path.exists(csv_path):
        return None
    
    data = {
        'zone_occupancy': defaultdict(list),
        'vehicle_occupancy': defaultdict(list),
        'total_booked': 0,
        'total_slots': 0,
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data['total_slots'] += 1
                
                booking_status = row.get('booking_status', 'Available')
                is_booked = 1 if booking_status == 'Booked' else 0
                
                if is_booked:
                    data['total_booked'] += 1
                
                zone = row.get('parking_zone', 'Zone-A')
                vehicle_type = row.get('vehicle_type', 'Four-Wheeler')
                priority = row.get('priority_level', 'Low')
                
                data['zone_occupancy'][zone].append(is_booked)
                data['vehicle_occupancy'][vehicle_type].append(is_booked)
        
        PARKING_DATA_CACHE = data
    except Exception as e:
        print(f"Error loading parking data: {e}")
        return None
    
    return data

def get_zone_availability(zone_name=None):
    """Calculate availability probability for a specific zone"""
    data = load_parking_data()
    
    if not data or not data['zone_occupancy']:
        return 0.5
    
    if zone_name and zone_name in data['zone_occupancy']:
        zone_data = data['zone_occupancy'][zone_name]
    else:
        all_data = []
        for zone_list in data['zone_occupancy'].values():
            all_data.extend(zone_list)
        zone_data = all_data
    
    if not zone_data:
        return 0.5
    
    booked_count = sum(zone_data)
    availability = 1.0 - (booked_count / len(zone_data))
    return round(availability, 3)

def get_vehicle_availability(vehicle_type=None):
    """Calculate availability probability for a specific vehicle type"""
    data = load_parking_data()
    
    if not data or not data['vehicle_occupancy']:
        return 0.5
    
    if vehicle_type and vehicle_type in data['vehicle_occupancy']:
        vehicle_data = data['vehicle_occupancy'][vehicle_type]
    else:
        all_data = []
        for vehicle_list in data['vehicle_occupancy'].values():
            all_data.extend(vehicle_list)
        vehicle_data = all_data
    
    if not vehicle_data:
        return 0.5
    
    booked_count = sum(vehicle_data)
    availability = 1.0 - (booked_count / len(vehicle_data))
    return round(availability, 3)

def predict_slot_availability(hour=None, weekday=None, occupied=None, total=None, zone=None, vehicle_type=None):
    """
    Predict slot availability based on dataset patterns
    
    Returns: probability (0.0 to 1.0) that a slot is available
    """
    
    data = load_parking_data()
    
    if data and data['total_slots'] > 0:
        zone_prob = get_zone_availability(zone)
        vehicle_prob = get_vehicle_availability(vehicle_type)
        
        combined_prob = (zone_prob + vehicle_prob) / 2
        
        if occupied is not None and total is not None and total > 0:
            occupancy_rate = occupied / total
            if occupancy_rate >= 0.85:
                combined_prob *= 0.5
        
        return combined_prob
    
    if total == 0:
        return 1.0
    
    occupancy_rate = occupied / total if (occupied is not None and total is not None) else 0.5
    
    threshold = 0.85
    
    if occupancy_rate >= threshold:
        return 0.0
    
    return 1.0 - (occupancy_rate * 0.5)
