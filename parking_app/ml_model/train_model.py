import joblib
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# =========================
# TRAINING DATA (EXAMPLE)
# =========================
# Each row:
# [hour, day, is_weekend, occupied_slots, total_slots, occupancy_ratio]

X = np.array([
    [8, 1, 0, 10, 60, 0.16],   # Morning, low occupancy → available
    [9, 1, 0, 15, 60, 0.25],   # Morning → available
    [10, 2, 0, 20, 60, 0.33],  # Late morning → available
    [12, 3, 0, 25, 60, 0.41],  # Noon → available

    [16, 4, 0, 40, 60, 0.66],  # Evening → borderline
    [17, 4, 0, 48, 60, 0.80],  # Peak → full
    [18, 5, 1, 52, 60, 0.86],  # Friday evening → full
    [19, 6, 1, 55, 60, 0.91],  # Weekend night → full
])

# Target:
# 1 = parking available
# 0 = parking full
y = np.array([
    1, 1, 1, 1,
    0, 0, 0, 0
])

# =========================
# TRAIN MODEL
# =========================
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

# =========================
# SAVE MODEL
# =========================
MODEL_PATH = os.path.join(os.path.dirname(__file__), "parking_model.pkl")
joblib.dump(model, MODEL_PATH)

print("✅ Model trained correctly with 6 features and saved.")

