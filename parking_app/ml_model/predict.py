import joblib
import os

# Load trained ML model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "parking_model.pkl")
model = joblib.load(MODEL_PATH)

def predict_slot_availability(hour, day, occupied_slots, total_slots):
    """
    ML Prediction:
    Returns:
    1 → Parking likely available
    0 → Parking likely full
    """

    if total_slots == 0:
        return 0

    is_weekend = 1 if day >= 5 else 0
    occupancy_ratio = occupied_slots / total_slots

    # ML input format
    X = [[
        hour,
        day,
        is_weekend,
        occupied_slots,
        total_slots,
        occupancy_ratio
    ]]

    prediction = model.predict(X)[0]
    return int(prediction)
