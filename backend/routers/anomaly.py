from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.ia.predict import predict_anomaly
from backend.models.models import Alert, AnomalyLog, MetricHistory
from backend.services.alerts_service import create_alert, get_setting_value

router = APIRouter(prefix="/anomaly", tags=["Anomalie"])


@router.post("/detect")
def detect_anomaly(db: Session = Depends(get_db)):
    last_metric = db.query(MetricHistory).order_by(
        MetricHistory.timestamp.desc()
    ).first()

    if last_metric:
        features = {
            "latency_ms": last_metric.latency_ms or 50,
            "nb_open_ports": 3,
            "nb_new_devices": 0,
            "nb_alerts_1h": db.query(Alert).filter(Alert.resolved == False).count(),
            "cpu_percent": last_metric.cpu_percent or 30,
            "ram_percent": last_metric.ram_percent or 40,
            "hour_of_day": datetime.now().hour,
        }
    else:
        features = {
            "latency_ms": 50,
            "nb_open_ports": 3,
            "nb_new_devices": 0,
            "nb_alerts_1h": 0,
            "cpu_percent": 30,
            "ram_percent": 40,
            "hour_of_day": datetime.now().hour,
        }

    result = predict_anomaly(features)

    latency_threshold = get_setting_value(db, "LATENCY_HIGH_THRESHOLD", 100)
    if features["latency_ms"] is not None and features["latency_ms"] > latency_threshold:
        create_alert(
            db,
            "LATENCY_HIGH",
            metadata={
                "latency_ms": features["latency_ms"],
                "threshold": latency_threshold,
            },
        )

    alert_id = None
    if result["is_anomaly"]:
        anomaly_threshold = get_setting_value(db, "ANOMALY_SCORE_THRESHOLD", 0.5)
        severity = "critical" if result["score"] >= anomaly_threshold else "warning"
        alert = create_alert(
            db,
            "ANOMALY_DETECTED",
            severity=severity,
            metadata={
                "score": result["score"],
                "confidence": result["confidence"],
            },
        )
        alert_id = alert.id

    log = AnomalyLog(
        features=features,
        score=result["score"],
        is_anomaly=result["is_anomaly"],
        alert_id=alert_id,
    )
    db.add(log)
    db.commit()

    return {
        "is_anomaly": result["is_anomaly"],
        "score": result["score"],
        "confidence": result["confidence"],
        "features_used": features,
        "alert_created": alert_id is not None,
    }


@router.get("/history")
def get_anomaly_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(AnomalyLog).order_by(
        AnomalyLog.timestamp.desc()
    ).offset(skip).limit(limit).all()
    return logs
