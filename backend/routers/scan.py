from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.models import Scan, ScanResult, Device, Alert
from schemas.scan import ScanRequest
from services.scanner import NetworkScanner
import asyncio, io, pandas as pd
from datetime import datetime

router = APIRouter(prefix="/scan", tags=["Scan"])
scanner = NetworkScanner()

async def run_scan(ip_range, scan_type, scan_id, db: Session):
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, scanner.scan, ip_range, scan_type)

    existing_ips = {d.ip for d in db.query(Device).all()}

    for r in results:
        r["is_new"] = r["ip"] not in existing_ips

        device = db.query(Device).filter(Device.ip == r["ip"]).first()
        if not device:
            device = Device(
                ip=r["ip"],
                hostname=r["hostname"],
                os_name=r["os_name"],
                device_type=r["device_type"],
                status="up" if r["state"] == "up" else "down"
            )
            db.add(device)
            db.flush()
            alert = Alert(
                type="NEW_UNKNOWN_DEVICE",
                severity="warning",
                message=f"Nouveau device détecté : {r['ip']} ({r['device_type']})",
                device_id=device.id
            )
            db.add(alert)
        else:
            device.hostname = r["hostname"]
            device.os_name = r["os_name"]
            device.device_type = r["device_type"]
            device.status = "up" if r["state"] == "up" else "down"
            device.last_seen = datetime.now()

        scan_result = ScanResult(
            scan_id=scan_id,
            device_ip=r["ip"],
            hostname=r["hostname"],
            os_name=r["os_name"],
            device_type=r["device_type"],
            ports=r["ports"],
            is_new=r["is_new"]
        )
        db.add(scan_result)

    scan_obj = db.query(Scan).filter(Scan.id == scan_id).first()
    scan_obj.finished_at = datetime.now()
    scan_obj.devices_found = len(results)
    db.commit()
    print(f"[SCAN {scan_id}] Terminé : {len(results)} devices")

@router.post("/start")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    scan = Scan(ip_range=request.ip_range, scan_type=request.scan_type)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    background_tasks.add_task(run_scan, request.ip_range, request.scan_type, scan.id, db)
    return {"scan_id": scan.id, "status": "en cours", "ip_range": request.ip_range}

@router.get("/history")
def get_scan_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(Scan.started_at.desc()).offset(skip).limit(limit).all()
    return scans

@router.get("/{scan_id}")
def get_scan_detail(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan introuvable")
    results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()
    return {"scan": scan, "devices": results}

@router.get("/{scan_id}/export")
def export_scan_csv(scan_id: int, db: Session = Depends(get_db)):
    results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="Scan introuvable ou vide")
    rows = []
    for r in results:
        ports_str = ", ".join([f"{p['port']}/{p['service']}" for p in (r.ports or [])])
        rows.append({
            "IP": r.device_ip,
            "Hostname": r.hostname,
            "OS": r.os_name,
            "Type": r.device_type,
            "Ports": ports_str,
            "Nouveau": "Oui" if r.is_new else "Non"
        })
    df = pd.DataFrame(rows)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.csv"}
    )