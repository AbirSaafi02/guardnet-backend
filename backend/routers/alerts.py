from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.models import Alert

router = APIRouter(prefix="/alerts", tags=["Alertes"])


@router.get("")
def list_alerts(
    type: str | None = Query(None),
    severity: str | None = Query(None),
    resolved: bool | None = Query(None),
    device_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
    if type:
        query = query.filter(Alert.type == type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    if device_id is not None:
        query = query.filter(Alert.device_id == device_id)

    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return alerts


@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    if alert.resolved:
        return {"message": "Alerte déjà résolue", "alert_id": alert_id}

    alert.resolved = True
    db.commit()
    db.refresh(alert)
    return {"message": "Alerte résolue", "alert_id": alert_id}


@router.get("/stats")
def alert_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Alert.id)).scalar() or 0
    unresolved = db.query(func.count(Alert.id)).filter(Alert.resolved == False).scalar() or 0
    per_type = {type_name: count for type_name, count in db.query(Alert.type, func.count(Alert.id)).group_by(Alert.type).all()}
    per_severity = {severity_name: count for severity_name, count in db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all()}
    return {
        "total": total,
        "unresolved": unresolved,
        "resolved": total - unresolved,
        "by_type": per_type,
        "by_severity": per_severity,
    }
