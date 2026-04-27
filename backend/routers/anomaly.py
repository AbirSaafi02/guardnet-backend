from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.models import Alert, AnomalyLog, MetricHistory
from ia.predict import predict_anomaly
from datetime import datetime, timezone

router = APIRouter(prefix="/anomaly", tags=["Anomalie"])

@router.post("/detect")
def detect_anomaly(db: Session = Depends(get_db)):
    # 1. Récupérer les dernières métriques depuis la DB
    last_metric = db.query(MetricHistory).order_by(
        MetricHistory.timestamp.desc()
    ).first()

    # 2. Si pas de métriques réelles → utiliser des valeurs par défaut
    if last_metric:
        features = {
            "latency_ms": last_metric.latency_ms or 50,
            "nb_open_ports": 3,
            "nb_new_devices": 0,
            "nb_alerts_1h": db.query(Alert).filter(
                Alert.resolved == False
            ).count(),
            "cpu_percent": last_metric.cpu_percent or 30,
            "ram_percent": last_metric.ram_percent or 40,
            "hour_of_day": datetime.now().hour
        }
    else:
        features = {
            "latency_ms": 50,
            "nb_open_ports": 3,
            "nb_new_devices": 0,
            "nb_alerts_1h": 0,
            "cpu_percent": 30,
            "ram_percent": 40,
            "hour_of_day": datetime.now().hour
        }

    # 3. Appeler le modèle IA
    result = predict_anomaly(features)

    # 4. Si anomalie → créer une alerte
    alert_id = None
    if result["is_anomaly"]:
        alert = Alert(
            type="ANOMALY_DETECTED",
            severity="critical",
            message=f"Anomalie détectée ! Score: {result['score']} Confiance: {result['confidence']}",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_id = alert.id

    # 5. Sauvegarder la prédiction dans AnomalyLog
    log = AnomalyLog(
        features=features,
        score=result["score"],
        is_anomaly=result["is_anomaly"],
        alert_id=alert_id
    )
    db.add(log)
    db.commit()

    return {
        "is_anomaly": result["is_anomaly"],
        "score": result["score"],
        "confidence": result["confidence"],
        "features_used": features,
        "alert_created": alert_id is not None
    }

@router.get("/history")
def get_anomaly_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(AnomalyLog).order_by(
        AnomalyLog.timestamp.desc()
    ).offset(skip).limit(limit).all()
    return logs