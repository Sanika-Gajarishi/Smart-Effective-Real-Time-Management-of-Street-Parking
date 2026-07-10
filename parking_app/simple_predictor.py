import json
from datetime import datetime

ZONE_PATTERNS = {
    'Zone-A': {
        'avg_occupancy': 0.762,
        'peak_occupancy': 0.994,
        'min_occupancy': 0.464,
        'peak_hours': [(9, 11), (14, 16), (17, 19)],
    },
    'Zone-B': {
        'avg_occupancy': 0.662,
        'peak_occupancy': 0.864,
        'min_occupancy': 0.403,
        'peak_hours': [(9, 11), (14, 16), (17, 19)],
    },
    'Zone-C': {
        'avg_occupancy': 0.662,
        'peak_occupancy': 0.864,
        'min_occupancy': 0.403,
        'peak_hours': [(9, 11), (14, 16), (17, 19)],
    },
    'Zone-D': {
        'avg_occupancy': 0.563,
        'peak_occupancy': 0.734,
        'min_occupancy': 0.403,
        'peak_hours': [(9, 11), (14, 16), (17, 19)],
    }
}

HOURLY_PATTERNS = {
    6: 0.464,
    7: 0.464,
    8: 0.464,
    9: 0.994,
    10: 0.994,
    11: 0.994,
    12: 0.464,
    13: 0.464,
    14: 0.994,
    15: 0.994,
    16: 0.994,
    17: 0.994,
    18: 0.994,
    19: 0.994,
    20: 0.464,
    21: 0.464,
}


def get_occupancy_for_zone(zone, hour):
    """Get occupancy rate for a specific zone and hour"""
    if zone not in ZONE_PATTERNS:
        return 0.5

    if hour in HOURLY_PATTERNS:
        base_occupancy = HOURLY_PATTERNS[hour]
    else:
        base_occupancy = ZONE_PATTERNS[zone]['avg_occupancy']

    zone_multiplier = 1.0
    if zone == 'Zone-A':
        zone_multiplier = 1.15
    elif zone == 'Zone-D':
        zone_multiplier = 0.85

    occupancy = min(base_occupancy * zone_multiplier, 1.0)
    return round(occupancy, 3)


def get_availability_prediction(hour=None, zone='Zone-A', vehicle_type=None, priority=None):
    """Get parking availability prediction for given parameters"""
    if hour is None:
        hour = datetime.now().hour

    occupancy_rate = get_occupancy_for_zone(zone, hour)
    available = occupancy_rate < 0.5
    probability = 1.0 - occupancy_rate if available else 0.0

    return {
        'available': available,
        'occupancy_rate': occupancy_rate,
        'probability': round(probability, 3),
        'confidence': 0.85,
        'hour': hour,
        'zone': zone
    }


def get_24hour_forecast(zone='Zone-A', vehicle_type=None, priority=None):
    """Get 24-hour forecast for a zone"""
    forecast = []
    for hour in range(6, 22):
        pred = get_availability_prediction(hour=hour, zone=zone)
        forecast.append({
            'hour': hour,
            'time': f'{hour:02d}:00',
            **pred
        })
    return forecast


def get_zone_statistics():
    """Get statistics for all zones"""
    stats = {}
    for zone in ZONE_PATTERNS.keys():
        occupancies = []
        for hour in range(6, 22):
            occ = get_occupancy_for_zone(zone, hour)
            occupancies.append(occ)

        stats[zone] = {
            'avg_occupancy': round(sum(occupancies) / len(occupancies), 3),
            'peak_occupancy': round(max(occupancies), 3),
            'min_occupancy': round(min(occupancies), 3),
            'std_dev': round(_calculate_std_dev(occupancies), 3)
        }

    return stats


def _calculate_std_dev(values):
    """Calculate standard deviation without numpy"""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5
