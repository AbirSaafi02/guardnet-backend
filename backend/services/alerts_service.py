from collections import defaultdict
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.models.models import Alert, Settings

ALERT_SEVERITY = {
    "DEVICE_DOWN": "critical",
    "NEW_DEVICE": "warning",
    "PORT_CHANGE": "warning",
    "PORT_SCAN_DETECTED": "critical",
    "ANOMALY_DETECTED": "critical",
    "NETWORK_OUTAGE": "critical",
    "LATENCY_HIGH": "warning",
}

ALERT_MESSAGES = {
    "DEVICE_DOWN": "Device {ip} est indisponible.",
    "NEW_DEVICE": "Nouveau device détecté : {ip} ({device_type}).",
    "PORT_CHANGE": "Changement de ports détecté pour {ip}. Ports ajoutés : {added}. Ports supprimés : {removed}.",
    "PORT_SCAN_DETECTED": "Scan de ports détecté sur {ip}.",
    "ANOMALY_DETECTED": "Anomalie détectée. Score: {score}, confiance: {confidence}.",
    "NETWORK_OUTAGE": "Panne réseau détectée.",
    "LATENCY_HIGH": "Latence élevée détectée : {latency_ms} ms (seuil {threshold} ms).",
}


def _parse_setting_value(value: str, default: Any) -> Any:
    if default is None:
        return value
    if isinstance(default, bool):
        return value.lower() in ("1", "true", "yes", "on")
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    if isinstance(default, float):
        try:
            return float(value)
        except ValueError:
            return default
    return value


def get_setting_value(db: Session, key: str, default: Any = None) -> Any:
    setting = db.query(Settings).filter(Settings.cle == key).first()
    if setting is None or setting.valeur is None:
        return default
    return _parse_setting_value(setting.valeur, default)


def _build_message(alert_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    metadata = metadata or {}
    template = ALERT_MESSAGES.get(alert_type, "Alerte {type} générée.")
    data = defaultdict(str, metadata)
    data["type"] = alert_type
    return template.format_map(data)


def create_alert(
    db: Session,
    alert_type: str,
    message: Optional[str] = None,
    severity: Optional[str] = None,
    device_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Alert:
    severity = severity or ALERT_SEVERITY.get(alert_type, "info")
    if message is None:
        message = _build_message(alert_type, metadata)

    alert = Alert(
        type=alert_type,
        severity=severity,
        message=message,
        device_id=device_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
