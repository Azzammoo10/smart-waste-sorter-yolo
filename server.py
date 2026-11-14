"""EcoVision ST-04 - FastAPI High-Performance Industrial Server.

Architecture:
- High-throughput MJPEG Video Stream with OpenCV / DirectShow.
- Real-time WebSocket Telemetry Broadcaster (30-60 FPS).
- REST Endpoints for Statistics, SQLite Journal, and File Uploads.
- Static hosting of React + Vite production build on root '/'.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import io
import json
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.camera import CameraManager
from src.config import (
    ACTIVE_CLASSES,
    CLASS_METADATA,
    DEFAULT_CONF_THRESHOLD,
    NATURE_COLORS,
    ROOT_DIR,
    SNAPSHOTS_DIR,
    WEIGHTS_PATH,
)
from src.database import (
    clear_database,
    get_detections_dataframe,
    get_recent_detections,
    get_statistics_summary,
    init_db,
    log_detection,
)
from src.detector import WasteDetector
from src.tracker import WasteTracker

init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Automatically launch the default web browser when the server is ready."""
    def _open():
        time.sleep(1.0)
        try:
            webbrowser.open("http://localhost:8000")
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()
    yield


app = FastAPI(
    title="EcoVision Industrial API",
    description="Backend API for YOLO Vision & Selective Waste Sorting Telemetry",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Vision & Telemetry State Manager
# ─────────────────────────────────────────────────────────────────────────────
class VisionRuntime:
    def __init__(self) -> None:
        self.camera_idx: int = 0
        self.conf_threshold: float = float(DEFAULT_CONF_THRESHOLD)
        self.auto_log: bool = True
        self.save_snapshots: bool = False
        self.camera: CameraManager | None = None
        self.detector = WasteDetector.get_instance(WEIGHTS_PATH)
        self.tracker = WasteTracker(window_size=5, min_stable_seconds=0.8, cooldown_seconds=2.5)

        self.is_running: bool = False
        self.latest_frame: np.ndarray | None = None
        self.latest_telemetry: dict[str, Any] = {
            "state": "IDLE",
            "stability": 0.0,
            "fps": 0.0,
            "active_object": None,
            "detections": [],
            "recent_logs": [],
        }
        self.fps: float = 0.0

    def start_camera(self, camera_idx: int = 0) -> bool:
        if self.camera is not None:
            self.camera.release()
        self.camera_idx = camera_idx
        self.camera = CameraManager(camera_index=camera_idx, width=640, height=480)
        self.is_running = self.camera.start()
        return self.is_running

    def stop_camera(self) -> None:
        self.is_running = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        self.tracker.reset()


runtime = VisionRuntime()


# ─────────────────────────────────────────────────────────────────────────────
# Streaming Video Feed (MJPEG)
# ─────────────────────────────────────────────────────────────────────────────
def generate_mjpeg_stream():
    """Generate continuous MJPEG frame stream with real-time HUD annotations."""
    if not runtime.is_running:
        runtime.start_camera(runtime.camera_idx)

    frame_count = 0
    prev_t = time.time()

    while runtime.is_running and runtime.camera is not None:
        ok, frame = runtime.camera.read_frame()
        if not ok or frame is None:
            time.sleep(0.02)
            continue

        frame_count += 1
        now = time.time()
        dt = now - prev_t
        if dt >= 1.0:
            runtime.fps = round(frame_count / dt, 1)
            frame_count = 0
            prev_t = now

        # Run YOLO detection
        detections = runtime.detector.predict(frame, conf_threshold=runtime.conf_threshold)

        # Update real-time tracker
        state, stability, active_object, events_to_log = runtime.tracker.update(detections)

        # Auto-log to SQLite on stable presentation
        if runtime.auto_log and events_to_log:
            for evt in events_to_log:
                s_path = None
                if runtime.save_snapshots:
                    s_name = f"snap_{int(time.time())}_{evt['class_name']}.jpg"
                    full_s = SNAPSHOTS_DIR / s_name
                    cv2.imwrite(str(full_s), frame)
                    s_path = str(full_s)
                log_detection(
                    class_name=evt["class_name"],
                    confidence=evt["confidence"],
                    source="webcam",
                    snapshot_path=s_path,
                )

        # Update live telemetry payload
        runtime.latest_telemetry = {
            "state": state,
            "stability": round(stability, 2),
            "fps": runtime.fps,
            "active_object": active_object,
            "detections": detections,
            "recent_logs": get_recent_detections(limit=5),
        }

        # Draw optical HUD
        annotated = runtime.detector.draw_live_hud(frame, state, stability, active_object, detections)
        runtime.latest_frame = annotated

        # Encode to JPEG
        ret, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        time.sleep(0.015)


@app.get("/api/video_feed")
def video_feed():
    """High-speed MJPEG video stream."""
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/camera/start")
def start_camera():
    """Start camera capture."""
    ok = runtime.start_camera(runtime.camera_idx)
    return {"status": "SUCCESS" if ok else "ERROR", "is_running": runtime.is_running}


@app.post("/api/camera/stop")
def stop_camera():
    """Stop camera capture and release device."""
    runtime.stop_camera()
    return {"status": "SUCCESS", "is_running": False}


@app.get("/api/camera/status")
def get_camera_status():
    """Get active camera status."""
    return {"is_running": runtime.is_running, "index": runtime.camera_idx}



# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────────────────────────────────────
class ConfigPayload(BaseModel):
    camera_idx: int = 0
    conf_threshold: float = 0.35
    auto_log: bool = True
    save_snapshots: bool = False


@app.get("/api/status")
def get_system_status():
    """Return system readiness, active model, and camera state."""
    return {
        "status": "ONLINE" if runtime.is_running else "READY",
        "model": {
            "name": "Détecteur Packaging 6 Classes (YOLO)",
            "weights": "waste_material_detector_best.pt",
            "classes": ACTIVE_CLASSES,
        },
        "camera": {
            "index": runtime.camera_idx,
            "active": runtime.is_running,
            "fps": runtime.fps,
        },
        "threshold": runtime.conf_threshold,
        "auto_log": runtime.auto_log,
        "taxonomy": CLASS_METADATA,
    }


@app.post("/api/config")
def update_config(payload: ConfigPayload):
    """Update runtime configuration dynamically."""
    if payload.camera_idx != runtime.camera_idx:
        runtime.start_camera(payload.camera_idx)
    runtime.conf_threshold = max(0.1, min(0.95, payload.conf_threshold))
    runtime.auto_log = payload.auto_log
    runtime.save_snapshots = payload.save_snapshots
    return {"status": "SUCCESS", "config": payload.model_dump()}


@app.get("/api/telemetry")
def get_telemetry():
    """Get current optical telemetry and active detection."""
    return runtime.latest_telemetry


@app.get("/api/detections")
def get_detections(limit: int = 100):
    """Retrieve recent confirmed detections from SQLite."""
    return get_recent_detections(limit=limit)


@app.get("/api/stats")
def get_stats():
    """Retrieve aggregated sorting statistics."""
    summary = get_statistics_summary()
    df = get_detections_dataframe()

    by_material: list[dict[str, Any]] = []
    if not df.empty and "display_name" in df.columns:
        counts = df["display_name"].value_counts().to_dict()
        by_material = [{"name": k, "count": v} for k, v in counts.items()]

    by_nature: list[dict[str, Any]] = []
    for nature, count in summary["by_nature"].items():
        by_nature.append({"name": nature, "count": count, "color": NATURE_COLORS.get(nature, "#388BFD")})

    return {
        "total_detections": summary["total_detections"],
        "avg_confidence": round(summary["avg_confidence"], 3),
        "most_common_waste": summary["most_common_waste"],
        "by_material": by_material,
        "by_nature": by_nature,
    }


@app.get("/api/export-csv")
def export_csv():
    """Export all SQLite entries to CSV."""
    df = get_detections_dataframe()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ecovision_registre_tri.csv"},
    )


@app.post("/api/detections/clear")
def purge_database():
    """Purge all entries from SQLite database."""
    clear_database()
    runtime.tracker.reset()
    return {"status": "SUCCESS", "message": "Base de données réinitialisée."}


@app.post("/api/upload")
async def analyze_uploaded_image(file: UploadFile = File(...)):
    """Analyze an uploaded static image for waste materials."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise HTTPException(status_code=400, detail="Image invalide ou format non supporté.")

    detections = runtime.detector.predict(img_bgr, conf_threshold=runtime.conf_threshold)

    # Convert annotated image to base64 or JPEG for preview
    annotated = runtime.detector.draw_detections(img_bgr, detections)
    ret, buffer = cv2.imencode(".jpg", annotated)
    img_bytes = buffer.tobytes() if ret else b""

    # Log to SQLite
    for d in detections:
        log_detection(
            class_name=d["class_name"],
            confidence=d["confidence"],
            source="upload",
        )

    return {
        "detections_count": len(detections),
        "detections": detections,
    }


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket Real-Time Telemetry Stream
# ─────────────────────────────────────────────────────────────────────────────
@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """High-frequency WebSocket channel pushing telemetry to React frontend."""
    await websocket.accept()
    try:
        while True:
            payload = runtime.latest_telemetry
            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(0.04)  # ~25 updates per second
    except WebSocketDisconnect:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Static File Hosting (Production React Build)
# ─────────────────────────────────────────────────────────────────────────────
frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists() and frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

