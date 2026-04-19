from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Settings
from dependencies.auth import get_current_user
router = APIRouter(prefix="/settings", tags=["Settings"])
@router.get("/thresholds")
def get_thresholds(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    thresholds = db.query(Settings).all()
    return {item.cle: item.valeur for item in thresholds}
@router.put("/thresholds")
def update_thresholds(
        data: dict,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    for cle, valeur in data.items():
        setting = db.query(Settings).filter(Settings.cle == cle).first()
        if setting:
            setting.valeur = str(valeur)
        else:
            new_setting = Settings(cle=cle, valeur=str(valeur))
            db.add(new_setting)
    db.commit()
    return {"message": "Seuils mis à jour"}