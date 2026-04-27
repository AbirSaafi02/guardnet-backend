from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import User
from pydantic import BaseModel
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True, encoding="utf-8-sig")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterRequest(BaseModel):
    email: str
    nom: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    ancien_password: str
    nouveau_password: str

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user = User(
        email=request.email,
        nom=request.nom,
        hashed_password=hash_password(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.email)
    return {"access_token": token, "token_type": "bearer", "nom": user.nom, "email": user.email}

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    token = create_token(user.id, user.email)
    return {"access_token": token, "token_type": "bearer", "nom": user.nom, "email": user.email}

@router.get("/me")
def get_me(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"email": user.email, "nom": user.nom}

@router.put("/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not verify_password(request.ancien_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    user.hashed_password = hash_password(request.nouveau_password)
    db.commit()
    return {"message": "Mot de passe changé avec succès"}
