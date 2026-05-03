import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

np.random.seed(42)

# Données NORMALES (900 exemples) — réseau calme
normal_data = {
    "latency_ms": np.random.normal(50, 5, 900),
    "nb_open_ports": np.random.randint(1, 5, 900),
    "nb_new_devices": np.zeros(900),
    "nb_alerts_1h": np.random.randint(0, 2, 900),
    "cpu_percent": np.random.normal(25, 5, 900),
    "ram_percent": np.random.normal(35, 5, 900),
    "hour_of_day": np.random.randint(8, 18, 900),
    "label": 1
}

# Données ANORMALES (100 exemples) — réseau suspect
anomaly_data = {
    "latency_ms": np.random.normal(800, 50, 100),
    "nb_open_ports": np.random.randint(30, 60, 100),
    "nb_new_devices": np.random.randint(8, 20, 100),
    "nb_alerts_1h": np.random.randint(15, 40, 100),
    "cpu_percent": np.random.normal(95, 2, 100),
    "ram_percent": np.random.normal(92, 2, 100),
    "hour_of_day": np.random.randint(0, 5, 100),
    "label": -1
}

df_normal = pd.DataFrame(normal_data)
df_anomaly = pd.DataFrame(anomaly_data)
df = pd.concat([df_normal, df_anomaly], ignore_index=True)

print(f"Dataset : {len(df)} exemples — {len(df_normal)} normaux + {len(df_anomaly)} anomalies")

features = ["latency_ms", "nb_open_ports", "nb_new_devices",
            "nb_alerts_1h", "cpu_percent", "ram_percent", "hour_of_day"]

X = df[features]
y = df["label"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = IsolationForest(
    contamination=0.1,
    random_state=42,
    n_estimators=200
)

model.fit(X_scaled)
predictions = model.predict(X_scaled)

print("\n=== RÉSULTATS ===")
print(confusion_matrix(y, predictions))
print(classification_report(y, predictions, target_names=["Anomalie", "Normal"]))

os.makedirs("ia", exist_ok=True)
joblib.dump(model, "ia/model.pkl")
joblib.dump(scaler, "ia/scaler.pkl")
print("✅ Modèle sauvegardé !")