from sqlalchemy.orm import Session
from models.models import User
from schemas.user import UserCreate, UserLogin
from core.security import hash_password, verify_password, create_access_token
def register_user(db: Session, data: UserCreate):
    exicting_user=db.query(User).filter(User.email==data.email).first()
    if(exicting_user):
        raise ValueError("Email déjà utilisé")
    # Hacher le password
    hashed = hash_password(data.password)

    # Créer l'utilisateur
    new_user = User(
        email=data.email,
        nom=data.nom,
        hashed_password=hashed
    )

    # Sauvegarder en base
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
def loginUser(db: Session, data: UserLogin):
    user=db.query(User).filter(User.email==data.email).first()
    if(user):
        if not verify_password(data.password,user.hashed_password):
            raise ValueError("Email ou password incorect ")
        token=create_access_token(data={"sub": str(user.id)})
        return token
    raise ValueError("Email ou password incorrect")




