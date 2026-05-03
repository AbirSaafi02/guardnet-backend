from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import User
from schemas.user import UserOut, UserCreate
from dependencies.auth import get_current_user
from schemas.user import UserOut, UserCreate, PasswordChange
from core.security import hash_password, verify_password
router = APIRouter(prefix="/users", tags=["Users"])
@router.get("/", response_model=list[UserOut])
def get_users(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    users = db.query(User).all()
    return users
@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
@router.put("/me/password")
def change_password(
        data: PasswordChange,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}
@router.delete("/{user_id}")
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}