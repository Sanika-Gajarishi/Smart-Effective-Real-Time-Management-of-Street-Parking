import os
import csv
import pickle
from datetime import datetime, timedelta
from collections import defaultdict
from django.conf import settings

NUMPY_AVAILABLE = False
SKLEARN_AVAILABLE = False
PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import LabelEncoder
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    RandomForestClassifier = None
    RandomForestRegressor = None
    LabelEncoder = None
    joblib = None

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


class AdvancedParkingPredictor:
    def __init__(self):
        self.model_dir = os.path.join(settings.BASE_DIR, 'parking_app', 'ml_model')
        self.data_dir = os.path.join(settings.BASE_DIR, 'data')
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.rf_model = None
        self.rf_prob_model = None
        self.encoders = {}
        self.zone_patterns = {}
        self.hourly_patterns = defaultdict(list)
        self.csv_path = os.path.join(self.data_dir, 'adypu_parking_users.csv')
        
    def load_and_prepare_data(self):
        """Load CSV and generate synthetic time-series data"""
        print("[INFO] Loading parking dataset...")
        
        if not os.path.exists(self.csv_path):
            print(f"[ERROR] Dataset not found at {self.csv_path}")
            return None
        
        df = pd.read_csv(self.csv_path)
        print(f"[OK] Loaded {len(df)} parking slots")
        
        synthetic_df = self._generate_synthetic_timeseries(df)
        return synthetic_df
    
    def _generate_synthetic_timeseries(self, df):
        """Generate 90 days of synthetic parking data with realistic patterns"""
        print("[PROGRESS] Generating synthetic time-series data...")
        
        records = []
        base_date = datetime.now() - timedelta(days=90)
        
        for day_offset in range(90):
            current_date = base_date + timedelta(days=day_offset)
            weekday = current_date.weekday()
            is_weekend = 1 if weekday >= 5 else 0
            
            for slot in df.itertuples():
                for hour in range(6, 22):
                    occupancy = self._calculate_occupancy(
                        hour=hour,
                        weekday=weekday,
                        zone=slot.parking_zone,
                        vehicle_type=slot.vehicle_type,
                        priority=slot.priority_level
                    )
                    
                    available = 1 if occupancy < 0.5 else 0
                    
                    records.append({
                        'date': current_date,
                        'hour': hour,
                        'weekday': weekday,
                        'is_weekend': is_weekend,
                        'zone': slot.parking_zone,
                        'vehicle_type': slot.vehicle_type,
                        'priority_level': slot.priority_level,
                        'occupancy_rate': occupancy,
                        'is_available': available
                    })
        
        synthetic_df = pd.DataFrame(records)
        print(f"[OK] Generated {len(synthetic_df)} time-series records")
        return synthetic_df
    
    def _calculate_occupancy(self, hour, weekday, zone, vehicle_type, priority):
        """Calculate realistic occupancy based on patterns"""
        
        base_occupancy = 0.5
        
        if weekday >= 5:
            base_occupancy *= 0.6
        else:
            base_occupancy *= 1.2
        
        if 9 <= hour <= 11 or 14 <= hour <= 16 or 17 <= hour <= 19:
            peak_factor = 1.5
        elif 6 <= hour < 9 or 11 < hour < 14 or 16 < hour < 17 or hour >= 20:
            peak_factor = 0.7
        else:
            peak_factor = 1.0
        
        base_occupancy *= peak_factor
        
        if priority.lower() == 'high':
            base_occupancy *= 1.3
        elif priority.lower() == 'low':
            base_occupancy *= 0.8
        
        if vehicle_type == 'Two-Wheeler':
            base_occupancy *= 0.7
        else:
            base_occupancy *= 1.2
        
        if zone == 'Zone-A':
            base_occupancy *= 1.15
        elif zone == 'Zone-D':
            base_occupancy *= 0.85
        
        return min(max(base_occupancy, 0.0), 1.0)
    
    def train_models(self):
        """Train Random Forest models for classification and probability"""
        print("\n[INFO] Training ML models...")
        
        synthetic_df = self.load_and_prepare_data()
        if synthetic_df is None:
            return False
        
        le_zone = LabelEncoder()
        le_vehicle = LabelEncoder()
        le_priority = LabelEncoder()
        le_weekday = LabelEncoder()
        
        synthetic_df['zone_encoded'] = le_zone.fit_transform(synthetic_df['zone'])
        synthetic_df['vehicle_encoded'] = le_vehicle.fit_transform(synthetic_df['vehicle_type'])
        synthetic_df['priority_encoded'] = le_priority.fit_transform(synthetic_df['priority_level'])
        synthetic_df['weekday_encoded'] = le_weekday.fit_transform(synthetic_df['weekday'])
        
        self.encoders = {
            'zone': le_zone,
            'vehicle': le_vehicle,
            'priority': le_priority,
            'weekday': le_weekday
        }
        
        features = ['hour', 'weekday_encoded', 'zone_encoded', 
                   'vehicle_encoded', 'priority_encoded', 'is_weekend']
        X = synthetic_df[features]
        y_classification = synthetic_df['is_available']
        y_regression = synthetic_df['occupancy_rate']
        
        print(f"[DATA] Training on {len(X)} samples with {len(features)} features")
        
        self.rf_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=15,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        self.rf_model.fit(X, y_classification)
        
        self.rf_prob_model = RandomForestRegressor(
            n_estimators=150,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        self.rf_prob_model.fit(X, y_regression)
        
        joblib.dump(self.rf_model, os.path.join(self.model_dir, 'rf_classifier.pkl'))
        joblib.dump(self.rf_prob_model, os.path.join(self.model_dir, 'rf_regressor.pkl'))
        joblib.dump(self.encoders, os.path.join(self.model_dir, 'encoders.pkl'))
        
        train_acc = self.rf_model.score(X, y_classification)
        print(f"[RESULT] Classification Accuracy: {train_acc:.2%}")
        
        self._print_feature_importance(features, self.rf_model.feature_importances_)
        
        self._analyze_patterns(synthetic_df)
        
        self.zone_patterns = synthetic_df.groupby('zone')['occupancy_rate'].agg(['mean', 'std']).to_dict()
        
        return True
    
    def _print_feature_importance(self, features, importances):
        """Print feature importance ranking"""
        print("\n[FEATURES] Feature Importance:")
        importance_df = pd.DataFrame({
            'feature': features,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        for idx, row in importance_df.iterrows():
            print(f"  {row['feature']}: {row['importance']:.2%}")
    
    def _analyze_patterns(self, df):
        """Analyze and display parking patterns"""
        print("\n[ANALYSIS] Parking Patterns Analysis:")
        
        hourly_avg = df.groupby('hour')['occupancy_rate'].mean()
        peak_hour = hourly_avg.idxmax()
        low_hour = hourly_avg.idxmin()
        
        print(f"  Peak Hour: {peak_hour}:00 ({hourly_avg[peak_hour]:.1%} occupancy)")
        print(f"  Lowest Hour: {low_hour}:00 ({hourly_avg[low_hour]:.1%} occupancy)")
        
        weekday_avg = df.groupby('weekday')['occupancy_rate'].mean()
        print(f"  Weekday Avg Occupancy: {weekday_avg[0]:.1%} (Monday)")
        print(f"  Weekend Avg Occupancy: {df[df['is_weekend']==1]['occupancy_rate'].mean():.1%}")
        
        zone_avg = df.groupby('zone')['occupancy_rate'].mean().sort_values(ascending=False)
        print(f"  Most Occupied Zone: {zone_avg.index[0]} ({zone_avg.iloc[0]:.1%})")
        print(f"  Least Occupied Zone: {zone_avg.index[-1]} ({zone_avg.iloc[-1]:.1%})")
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            self.rf_model = joblib.load(os.path.join(self.model_dir, 'rf_classifier.pkl'))
            self.rf_prob_model = joblib.load(os.path.join(self.model_dir, 'rf_regressor.pkl'))
            self.encoders = joblib.load(os.path.join(self.model_dir, 'encoders.pkl'))
            print("[OK] Models loaded successfully")
            return True
        except Exception as e:
            print(f"[WARNING] Could not load models: {e}")
            return False
    
    def predict_availability(self, hour, zone=None, vehicle_type=None, priority=None, date=None):
        """
        Predict if parking is available at specific hour
        
        Returns:
        {
            'available': bool,
            'probability': float (0-1),
            'occupancy_rate': float (0-1),
            'confidence': float (0-1)
        }
        """
        
        if self.rf_model is None:
            if not self.load_models():
                return self._fallback_prediction(hour, zone)
        
        if date is None:
            date = datetime.now()
        
        weekday = date.weekday()
        is_weekend = 1 if weekday >= 5 else 0
        
        if zone is None:
            zone = 'Zone-A'
        if vehicle_type is None:
            vehicle_type = 'Four-Wheeler'
        if priority is None:
            priority = 'Low'
        
        try:
            zone_encoded = self.encoders['zone'].transform([zone])[0]
            vehicle_encoded = self.encoders['vehicle'].transform([vehicle_type])[0]
            priority_encoded = self.encoders['priority'].transform([priority])[0]
            weekday_encoded = self.encoders['weekday'].transform([weekday])[0]
        except:
            return self._fallback_prediction(hour, zone)
        
        X = np.array([[hour, weekday_encoded, zone_encoded, vehicle_encoded, 
                      priority_encoded, is_weekend]])
        
        availability = self.rf_model.predict(X)[0]
        probability = self.rf_model.predict_proba(X)[0][1]
        occupancy = self.rf_prob_model.predict(X)[0]
        occupancy = max(min(occupancy, 1.0), 0.0)
        
        confidence = max(abs(probability - 0.5) * 2, 0.5)
        
        return {
            'available': bool(availability),
            'probability': round(probability, 3),
            'occupancy_rate': round(occupancy, 3),
            'confidence': round(confidence, 3),
            'hour': hour,
            'zone': zone,
            'vehicle_type': vehicle_type
        }
    
    def forecast_24hours(self, zone=None, vehicle_type=None, priority=None):
        """Predict availability for next 24 hours"""
        
        now = datetime.now()
        start_hour = now.hour + 1
        
        forecast = []
        for offset in range(24):
            hour = (start_hour + offset) % 24
            pred_date = now + timedelta(hours=offset+1)
            
            prediction = self.predict_availability(
                hour=hour,
                zone=zone,
                vehicle_type=vehicle_type,
                priority=priority,
                date=pred_date
            )
            
            forecast.append({
                **prediction,
                'timestamp': pred_date.isoformat(),
                'time_readable': pred_date.strftime('%I:%M %p')
            })
        
        return forecast
    
    def get_zone_statistics(self):
        """Get occupancy statistics by zone"""
        
        if self.rf_prob_model is None:
            if not self.load_models():
                return {}
        
        zones = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D']
        stats = {}
        
        for zone in zones:
            predictions = []
            for hour in range(6, 22):
                pred = self.predict_availability(hour=hour, zone=zone)
                predictions.append(pred['occupancy_rate'])
            
            stats[zone] = {
                'avg_occupancy': round(np.mean(predictions), 3),
                'peak_occupancy': round(np.max(predictions), 3),
                'min_occupancy': round(np.min(predictions), 3),
                'std_dev': round(np.std(predictions), 3)
            }
        
        return stats
    
    def _fallback_prediction(self, hour, zone=None):
        """Fallback rule-based prediction"""
        
        if 9 <= hour <= 11 or 14 <= hour <= 16 or 17 <= hour <= 19:
            occupancy = 0.75
        elif 6 <= hour < 9 or 20 <= hour <= 22:
            occupancy = 0.35
        else:
            occupancy = 0.5
        
        if zone == 'Zone-A':
            occupancy = min(occupancy * 1.15, 1.0)
        
        availability = occupancy < 0.5
        
        return {
            'available': availability,
            'probability': round(1.0 - occupancy, 3),
            'occupancy_rate': round(occupancy, 3),
            'confidence': 0.5,
            'hour': hour,
            'zone': zone or 'Zone-A'
        }


def train_advanced_models():
    """Train all advanced prediction models"""
    predictor = AdvancedParkingPredictor()
    return predictor.train_models()


def get_availability_prediction(hour, zone=None, vehicle_type=None, priority=None):
    """Get prediction for specific parameters"""
    predictor = AdvancedParkingPredictor()
    predictor.load_models()
    return predictor.predict_availability(hour, zone, vehicle_type, priority)


def get_24hour_forecast(zone=None, vehicle_type=None, priority=None):
    """Get 24-hour forecast"""
    predictor = AdvancedParkingPredictor()
    predictor.load_models()
    return predictor.forecast_24hours(zone, vehicle_type, priority)
