import csv
import os
from django.conf import settings

CSV_PATH = os.path.join(
    settings.BASE_DIR,
    "parking_app",
    "data",
    "adypu_parking_users.csv"
)

def load_adypu_users():
    users = []

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append({
                "user_id": row.get("user_id"),
                "name": row.get("name"),
                "role": row.get("role"),   # student / staff / faculty
                "vehicle_type": row.get("vehicle_type"),
                "vehicle_number": row.get("vehicle_number"),
            })

    return users

