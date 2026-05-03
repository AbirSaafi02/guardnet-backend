from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import models
from routers import scan, auth, users, settings, anomaly

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuardNet API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings.router)
app.include_router(anomaly.router)

@app.get("/")
def root():
    return {"message": "GuardNet API operationnelle"}