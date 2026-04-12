from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import models
from routers import auth, users, settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuardNet API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#app.include_router(scan.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings.router)

@app.get("/")
def root():
    return {"message": "GuardNet API operationnelle"}