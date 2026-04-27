from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nom = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, unique=True, index=True)
    hostname = Column(String, nullable=True)
    os_name = Column(String, nullable=True)
    device_type = Column(String, default="unknown")
    status = Column(String, default="unknown")
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, nullable=True)
    alerts = relationship("Alert", back_populates="device")

class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    ip_range = Column(String, nullable=False)
    scan_type = Column(String, default="rapide")
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
    devices_found = Column(Integer, default=0)

class ScanResult(Base):
    __tablename__ = "scan_results"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    device_ip = Column(String)
    hostname = Column(String, nullable=True)
    os_name = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    ports = Column(JSON)
    is_new = Column(Boolean, default=False)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    severity = Column(String)
    message = Column(Text)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    device = relationship("Device", back_populates="alerts")
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class MetricHistory(Base):
    __tablename__ = "metric_history"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    timestamp = Column(DateTime, server_default=func.now())
    latency_ms = Column(Float, nullable=True)
    is_up = Column(Boolean)
    cpu_percent = Column(Float, nullable=True)
    ram_percent = Column(Float, nullable=True)

class TrafficMetric(Base):
    __tablename__ = "traffic_metrics"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    total_packets = Column(Integer)
    tcp_pct = Column(Float)
    udp_pct = Column(Float)
    bytes_total = Column(Integer)
    top_ips = Column(JSON)
    top_ports = Column(JSON)

class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    features = Column(JSON)
    score = Column(Float)
    is_anomaly = Column(Boolean)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    cle = Column(String, unique=True)
    valeur = Column(String)