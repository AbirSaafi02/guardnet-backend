import pandas as pd
import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = joblib.load(os.path.join(BASE_DIR, "model.pkl"))
scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))

FEATURES = ["latency_ms", "nb_open_ports", "nb_new_devices",
            "nb_alerts_1h", "cpu_percent", "ram_percent", "hour_of_day"]

def predict_anomaly(features_dict: dict) -> dict:
    df = pd.DataFrame([features_dict])[FEATURES]
    df_scaled = scaler.transform(df)
    prediction = model.predict(df_scaled)[0]
    score = -model.score_samples(df_scaled)[0]

    if score > 0.6:
        confidence = "high"
    elif score > 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "is_anomaly": bool(prediction == -1),  # ← converti en bool Python
        "score": round(float(score), 4),        # ← converti en float Python
        "confidence": confidence,
        "prediction_raw": int(prediction)       # ← converti en int Python
    }