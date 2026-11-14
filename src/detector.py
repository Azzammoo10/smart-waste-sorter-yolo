"""YOLOv8 8-class Waste Object Detector with styled bounding boxes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

from src.config import (
    CLASS_MIN_CONF_THRESHOLDS,
    DEFAULT_CONF_THRESHOLD,
    DEFAULT_IOU_THRESHOLD,
    WEIGHTS_PATH,
    get_class_info,
)


def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """Convert hex string (e.g. #F1C40F) to OpenCV BGR tuple."""
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) != 6:
        return (50, 190, 90)
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return (b, g, r)


class WasteDetector:
    """Wraps YOLOv8 model for waste detection and visualization."""

    _instances: dict[str, WasteDetector] = {}

    def __init__(self, weights_path: Path | str | None = None) -> None:
        self.weights_path = Path(weights_path) if weights_path else WEIGHTS_PATH
        if not self.weights_path.is_file():
            raise FileNotFoundError(f"Modèle YOLO introuvable : {self.weights_path}")
        self.model = YOLO(str(self.weights_path))

    @classmethod
    def get_instance(cls, weights_path: Path | str | None = None) -> WasteDetector:
        """Cache instances by weights path to avoid re-reading weights."""
        target_path = Path(weights_path) if weights_path else WEIGHTS_PATH
        key = str(target_path.resolve())
        if key not in cls._instances:
            cls._instances[key] = cls(target_path)
        return cls._instances[key]

    def predict(
        self,
        frame: np.ndarray,
        conf_threshold: float = DEFAULT_CONF_THRESHOLD,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        imgsz: int = 640,
    ) -> list[dict[str, Any]]:
        """Run object detection on an input frame (BGR numpy array).

        Returns:
            List of structured detections.
        """
        # Case 1: Classification model (e.g. best.pt from TrashNet)
        if getattr(self.model, "task", "") == "classify":
            results = self.model.predict(
                source=frame,
                imgsz=224,
                verbose=False,
                device="cpu",
            )[0]
            if results.probs is None:
                return []
            top1_idx = int(results.probs.top1)
            conf = float(results.probs.top1conf)
            if conf < float(conf_threshold):
                return []

            if isinstance(self.model.names, dict):
                raw_name = str(self.model.names.get(top1_idx, top1_idx)).lower()
            elif isinstance(self.model.names, (list, tuple)) and top1_idx < len(self.model.names):
                raw_name = str(self.model.names[top1_idx]).lower()
            else:
                raw_name = f"class_{top1_idx}"

            info = get_class_info(raw_name)
            h, w = frame.shape[:2]
            # Visual bounding frame
            coords = (int(w * 0.15), int(h * 0.08), int(w * 0.85), int(h * 0.92))

            return [
                {
                    "box": coords,
                    "class_name": raw_name,
                    "confidence": round(conf, 4),
                    "display_name": info["display_name"],
                    "bin_label": info["bin_label"],
                    "bin_color": info["bin_color"],
                    "waste_nature": info["waste_nature"],
                    "icon": info["icon"],
                }
            ]

        # Case 2: Object detection model (e.g. YOLOv8 / YOLO11 detection)
        results = self.model.predict(
            source=frame,
            conf=float(conf_threshold),
            iou=float(iou_threshold),
            agnostic_nms=True,  # Prevent multiple overlapping class boxes on the same object
            imgsz=imgsz,
            verbose=False,
            device="cpu",
        )[0]

        detections: list[dict[str, Any]] = []
        if results.boxes is None or len(results.boxes) == 0:
            return detections

        for box in results.boxes:
            coords = [int(round(v)) for v in box.xyxy[0].detach().cpu().tolist()]
            conf = float(box.conf[0].detach().cpu())
            cls_idx = int(box.cls[0].detach().cpu())

            # Retrieve class name
            if isinstance(self.model.names, dict):
                raw_name = str(self.model.names.get(cls_idx, cls_idx)).lower()
            elif isinstance(self.model.names, (list, tuple)) and cls_idx < len(self.model.names):
                raw_name = str(self.model.names[cls_idx]).lower()
            else:
                raw_name = f"class_{cls_idx}"

            # Filter out detections below class-specific thresholds
            # (e.g. medical_waste requires higher confidence to prevent false alarms from human faces)
            min_required_conf = max(
                float(conf_threshold), CLASS_MIN_CONF_THRESHOLDS.get(raw_name, 0.0)
            )
            if conf < min_required_conf:
                continue

            info = get_class_info(raw_name)

            detections.append(
                {
                    "box": tuple(coords),  # (x1, y1, x2, y2)
                    "class_name": raw_name,
                    "confidence": round(conf, 4),
                    "display_name": info["display_name"],
                    "bin_label": info["bin_label"],
                    "bin_color": info["bin_color"],
                    "waste_nature": info["waste_nature"],
                    "icon": info["icon"],
                }
            )

        return detections

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: list[dict[str, Any]],
    ) -> np.ndarray:
        """Draw clean, industrial vision bounding boxes and HUD overlays."""
        output = frame.copy()
        height, width = output.shape[:2]

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            color = hex_to_bgr(det.get("bin_color", "#388BFD"))
            conf = det["confidence"]
            display_name = det["display_name"]
            bin_label = det["bin_label"]

            # Main bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

            # Industrial corner reticles
            c_len = min(20, max(6, int((x2 - x1) * 0.15)), max(6, int((y2 - y1) * 0.15)))
            cv2.line(output, (x1, y1), (x1 + c_len, y1), (255, 255, 255), 2)
            cv2.line(output, (x1, y1), (x1, y1 + c_len), (255, 255, 255), 2)
            cv2.line(output, (x2, y1), (x2 - c_len, y1), (255, 255, 255), 2)
            cv2.line(output, (x2, y1), (x2, y1 + c_len), (255, 255, 255), 2)
            cv2.line(output, (x1, y2), (x1 + c_len, y2), (255, 255, 255), 2)
            cv2.line(output, (x1, y2), (x1, y2 - c_len), (255, 255, 255), 2)
            cv2.line(output, (x2, y2), (x2 - c_len, y2), (255, 255, 255), 2)
            cv2.line(output, (x2, y2), (x2, y2 - c_len), (255, 255, 255), 2)

            # Industrial Tag Label
            label = f"{display_name.upper()} [{conf:.0%}] -> {bin_label.upper()}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.46
            thickness = 1
            (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            badge_y = max(th + baseline + 8, y1)
            cv2.rectangle(
                output,
                (x1, badge_y - th - baseline - 5),
                (min(x1 + tw + 8, width - 1), badge_y + 2),
                color,
                -1,
            )
            cv2.putText(
                output,
                label,
                (x1 + 4, badge_y - 3),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

        return output

    def draw_live_hud(
        self,
        frame: np.ndarray,
        state: str,
        stability: float,
        active_object: dict[str, Any] | None,
        detections: list[dict[str, Any]],
    ) -> np.ndarray:
        """Render real-time, responsive optical telemetry HUD onto camera frame."""
        output = frame.copy()
        height, width = output.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX

        # ── State 1 : IDLE (Targeting Reticle) ──────────────────────────────
        if state == "IDLE" or active_object is None:
            cx, cy = width // 2, height // 2
            rw, rh = int(width * 0.50), int(height * 0.65)
            x1, y1 = cx - rw // 2, cy - rh // 2
            x2, y2 = cx + rw // 2, cy + rh // 2

            c_len = 26
            guide_col = (180, 195, 205)  # Subtle slate
            for p1, p2, p3, p4 in [
                ((x1, y1), (x1 + c_len, y1), (x1, y1), (x1, y1 + c_len)),
                ((x2, y1), (x2 - c_len, y1), (x2, y1), (x2, y1 + c_len)),
                ((x1, y2), (x1 + c_len, y2), (x1, y2), (x1, y2 - c_len)),
                ((x2, y2), (x2 - c_len, y2), (x2, y2), (x2, y2 - c_len)),
            ]:
                cv2.line(output, p1, p2, guide_col, 2)
                cv2.line(output, p3, p4, guide_col, 2)

            cv2.putText(
                output,
                "ZONE D'INSPECTION // PRESENTER UN EMBALLAGE",
                (x1 + 14, cy),
                font,
                0.45,
                (220, 230, 240),
                1,
                cv2.LINE_AA,
            )
            return output

        # ── State 2 : TRACKING (Real-Time Live Response) ────────────────────
        x1, y1, x2, y2 = active_object["box"]
        # Ensure within image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width - 1, x2), min(height - 1, y2)

        color = hex_to_bgr(active_object.get("bin_color", "#2563EB"))
        conf = active_object.get("confidence", 0.0)
        disp_name = active_object.get("display_name", "DECHET").upper()
        bin_label = active_object.get("bin_label", "BAC DE TRI").upper()

        # Bounding box
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

        # High-tech corners
        c_len = min(24, max(8, int((x2 - x1) * 0.2)), max(8, int((y2 - y1) * 0.2)))
        for p1, p2, p3, p4 in [
            ((x1, y1), (x1 + c_len, y1), (x1, y1), (x1, y1 + c_len)),
            ((x2, y1), (x2 - c_len, y1), (x2, y1), (x2, y1 + c_len)),
            ((x1, y2), (x1 + c_len, y2), (x1, y2), (x1, y2 - c_len)),
            ((x2, y2), (x2 - c_len, y2), (x2, y2), (x2, y2 - c_len)),
        ]:
            cv2.line(output, p1, p2, (255, 255, 255), 2)
            cv2.line(output, p3, p4, (255, 255, 255), 2)

        # Top Badge: Class Name + Confidence
        label_text = f"{disp_name} [{conf:.0%}]"
        (tw, th), bl = cv2.getTextSize(label_text, font, 0.48, 1)
        badge_y = max(th + bl + 8, y1)
        cv2.rectangle(output, (x1, badge_y - th - bl - 5), (min(x1 + tw + 10, width - 1), badge_y + 2), color, -1)
        cv2.putText(output, label_text, (x1 + 5, badge_y - 3), font, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

        # Bottom Badge: Bin Destination
        dest_text = f"DESTINATION: {bin_label}"
        (dw, dh), dbl = cv2.getTextSize(dest_text, font, 0.44, 1)
        bot_y = min(height - 10, y2 + dh + dbl + 6)
        cv2.rectangle(output, (x1, y2 + 2), (min(x1 + dw + 10, width - 1), bot_y), (15, 23, 42), -1)
        cv2.putText(output, dest_text, (x1 + 5, bot_y - 4), font, 0.44, (255, 255, 255), 1, cv2.LINE_AA)

        # Telemetry: Stability tag in top corner
        stab_text = f"STABILITE DU SIGNAL: {int(stability * 100)}%"
        (sw, sh), sbl = cv2.getTextSize(stab_text, font, 0.40, 1)
        cv2.rectangle(output, (width - sw - 20, 10), (width - 10, 10 + sh + sbl + 6), (15, 23, 42), -1)
        stab_col = (50, 205, 50) if stability >= 0.8 else (0, 190, 255)
        cv2.putText(output, stab_text, (width - sw - 15, 10 + sh + 3), font, 0.40, stab_col, 1, cv2.LINE_AA)

        return output

    def draw_temporal_hud(
        self,
        frame: np.ndarray,
        state: str,
        progress: float,
        active_verdict: dict[str, Any] | None,
        detections: list[dict[str, Any]],
    ) -> np.ndarray:
        """Backward-compatible alias routing to draw_live_hud."""
        return self.draw_live_hud(frame, state, progress, active_verdict, detections)



