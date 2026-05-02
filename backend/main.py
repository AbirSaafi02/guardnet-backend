from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import SessionLocal, engine
from backend.models import models
from backend.routers import alerts, anomaly, auth, monitoring, scan, settings, users
from backend.services import monitoring_service

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuardNet API", version="1.0")

scheduler = BackgroundScheduler()


def _run_scheduled_anomaly() -> None:
    db = SessionLocal()
    try:
        anomaly.detect_anomaly(db=db)
    except Exception as exc:
        print(f"[SCHEDULER] Echec de la detection automatique : {exc}")
    finally:
        db.close()


@app.on_event("startup")
def start_scheduler() -> None:
    scheduler.add_job(
        _run_scheduled_anomaly,
        trigger="interval",
        minutes=5,
        id="anomaly_detection",
        replace_existing=True,
    )
    scheduler.start()


@app.on_event("shutdown")
def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(settings.router)
app.include_router(anomaly.router)
app.include_router(monitoring.router)
app.include_router(alerts.router)


@app.get("/")
def root():
    return {"message": "GuardNet API operationnelle"}
