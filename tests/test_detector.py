"""Unit tests for YOLOv8 detector and taxonomy mappings."""
from pathlib import Path
import cv2
import numpy as np
import pytest

from src.config import CLASS_METADATA, WEIGHTS_PATH, get_class_info
from src.detector import WasteDetector, hex_to_bgr
from src.tracker import WasteTracker


def test_taxonomy_mappings():
    """Verify that all 8 classes have valid French names and bins."""
    expected_classes = [
        "plastic", "metal", "glass", "e_waste",
        "medical_waste", "paper", "cardboard", "organic_waste"
    ]
    for cls in expected_classes:
        info = get_class_info(cls)
        assert "display_name" in info
        assert "bin_label" in info
        assert "bin_color" in info
        assert "waste_nature" in info


def test_hex_to_bgr():
    """Verify HEX color conversion to OpenCV BGR."""
    bgr = hex_to_bgr("#F1C40F")
    assert bgr == (15, 196, 241)  # Hex F1 C4 0F in BGR


def test_tracker_realtime_stabilization():
    """Verify tracker real-time responsive tracking, class switching, and debounced logging."""
    import time
    tracker = WasteTracker(window_size=4, min_stable_seconds=0.15, cooldown_seconds=1.0)
    
    mock_paper = [
        {
            "class_name": "paper",
            "confidence": 0.90,
            "box": (10, 10, 100, 100),
            "display_name": "Papier",
            "bin_label": "Bac Jaune",
            "bin_color": "#A371F7",
            "waste_nature": "Recyclable",
        }
    ]
    mock_carton = [
        {
            "class_name": "cardboard",
            "confidence": 0.95,
            "box": (12, 12, 110, 110),
            "display_name": "Carton",
            "bin_label": "Bac Jaune",
            "bin_color": "#D29922",
            "waste_nature": "Recyclable",
        }
    ]

    # Frame 1: Immediate tracking, no blocking
    state, stability, active_obj, events = tracker.update(mock_paper)
    assert state == "TRACKING"
    assert active_obj is not None
    assert active_obj["class_name"] == "paper"
    assert len(events) == 0

    # Wait for stable logging duration
    time.sleep(0.2)
    state, stability, active_obj, events = tracker.update(mock_paper)
    assert state == "TRACKING"
    assert len(events) == 1  # Logged once!
    assert events[0]["class_name"] == "paper"

    # Immediate next frame with same object: no duplicate log
    state, stability, active_obj, events = tracker.update(mock_paper)
    assert len(events) == 0

    # Immediate switch to carton: NO FREEZE! Immediately tracks carton
    state, stability, active_obj, events = tracker.update(mock_carton)
    assert state == "TRACKING"
    assert active_obj is not None
    # Feed another frame to establish dominant class in window
    state, stability, active_obj, events = tracker.update(mock_carton)
    assert active_obj["class_name"] == "cardboard"  # Successfully switched without getting stuck!

    # When object removed (3 empty frames) -> reset to IDLE
    tracker.update([])
    tracker.update([])
    state, stability, active_obj, events = tracker.update([])
    assert state == "IDLE"
    assert active_obj is None



def test_detector_inference():
    """Verify YOLO model loads and runs inference on an image."""
    assert WEIGHTS_PATH.is_file(), f"Missing model: {WEIGHTS_PATH}"
    detector = WasteDetector.get_instance()

    # Create synthetic test frame
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.predict(test_img, conf_threshold=0.10)
    assert isinstance(detections, list)

    # Test drawing
    annotated = detector.draw_detections(test_img, detections)
    assert annotated.shape == test_img.shape

