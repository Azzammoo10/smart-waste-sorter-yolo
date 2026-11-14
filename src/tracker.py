"""High-Performance Real-Time Optical Stabilization & Tracking Engine.

Provides responsive, fluid, real-time waste tracking:
- Zero freeze / non-blocking continuous inference stream.
- Temporal sliding-window smoothing (anti-jitter on bounding boxes and class labels).
- Instantaneous reaction when the user changes objects (e.g. paper -> carton).
- Intelligent logging debounce: records confirmed items to SQLite once per stable presentation.
"""
from __future__ import annotations

import time
from collections import Counter, deque
from typing import Any


class WasteTracker:
    """Real-time responsive stabilization tracker with anti-jitter and smart logging."""

    def __init__(
        self,
        window_size: int = 6,
        min_stable_seconds: float = 0.8,
        cooldown_seconds: float = 3.0,
    ) -> None:
        self.window_size = window_size
        self.min_stable_seconds = min_stable_seconds
        self.cooldown_seconds = cooldown_seconds

        # Sliding window of recent detections
        self.history: deque[dict[str, Any]] = deque(maxlen=window_size)
        self.empty_frames_count: int = 0

        # Current stable tracking state
        self.current_class: str | None = None
        self.class_first_seen_time: float = 0.0
        self.last_log_time: float = 0.0
        self.current_logged_for_this_item: bool = False

        # Smoothed bounding box (x1, y1, x2, y2)
        self.smoothed_box: tuple[int, int, int, int] | None = None

    def update(
        self, current_detections: list[dict[str, Any]]
    ) -> tuple[str, float, dict[str, Any] | None, list[dict[str, Any]]]:
        """Update tracker with detections from current frame.

        Args:
            current_detections: List of detections from YOLO for current frame.

        Returns:
            Tuple of:
            - state: "TRACKING" (object present) or "IDLE" (zone free)
            - stability: float from 0.0 to 1.0 (agreement ratio over recent frames)
            - active_object: dict with smoothed detection data, or None
            - events_to_log: list of confirmed detections to insert into SQLite
        """
        now = time.time()
        events_to_log: list[dict[str, Any]] = []

        if not current_detections:
            self.empty_frames_count += 1
            if self.empty_frames_count >= 3:
                # Reset tracking history if zone is empty
                self.history.clear()
                self.current_class = None
                self.smoothed_box = None
                self.current_logged_for_this_item = False
                return "IDLE", 0.0, None, events_to_log

            # Brief drop (< 3 frames): maintain last smoothed object if available
            if self.history:
                last_obj = dict(self.history[-1])
                if self.smoothed_box:
                    last_obj["box"] = self.smoothed_box
                return "TRACKING", 0.5, last_obj, events_to_log
            return "IDLE", 0.0, None, events_to_log

        # Object is present
        self.empty_frames_count = 0
        top_detection = current_detections[0]
        self.history.append(top_detection)

        # 1. Determine dominant class in sliding window (majority voting)
        classes_in_window = [d["class_name"] for d in self.history]
        counts = Counter(classes_in_window)
        dominant_class, dominant_count = counts.most_common(1)[0]
        stability = dominant_count / len(self.history)

        # 2. Track class changes and duration
        if dominant_class != self.current_class:
            self.current_class = dominant_class
            self.class_first_seen_time = now
            self.current_logged_for_this_item = False
            self.smoothed_box = top_detection["box"]

        # 3. Smooth bounding box coordinates using Exponential Moving Average (EMA)
        raw_box = top_detection["box"]
        if self.smoothed_box is None:
            self.smoothed_box = raw_box
        else:
            alpha = 0.65  # 65% new, 35% previous (fast response + no jitter)
            sx1 = int(round(alpha * raw_box[0] + (1 - alpha) * self.smoothed_box[0]))
            sy1 = int(round(alpha * raw_box[1] + (1 - alpha) * self.smoothed_box[1]))
            sx2 = int(round(alpha * raw_box[2] + (1 - alpha) * self.smoothed_box[2]))
            sy2 = int(round(alpha * raw_box[3] + (1 - alpha) * self.smoothed_box[3]))
            self.smoothed_box = (sx1, sy1, sx2, sy2)

        # 4. Construct active smoothed object
        active_object = dict(top_detection)
        active_object["box"] = self.smoothed_box
        active_object["stability"] = round(stability, 2)

        # Average confidence of dominant class in window
        dominant_samples = [d for d in self.history if d["class_name"] == dominant_class]
        avg_conf = sum(d["confidence"] for d in dominant_samples) / len(dominant_samples)
        active_object["confidence"] = round(avg_conf, 3)

        # 5. Smart Logging Debounce
        stable_duration = now - self.class_first_seen_time
        time_since_last_log = now - self.last_log_time

        # If item has been stable for min_stable_seconds and hasn't been logged yet
        if (
            stability >= 0.65
            and stable_duration >= self.min_stable_seconds
            and not self.current_logged_for_this_item
            and time_since_last_log >= self.cooldown_seconds
        ):
            events_to_log.append(active_object)
            self.current_logged_for_this_item = True
            self.last_log_time = now

        return "TRACKING", stability, active_object, events_to_log

    def reset(self) -> None:
        """Clear all tracking state."""
        self.history.clear()
        self.empty_frames_count = 0
        self.current_class = None
        self.class_first_seen_time = 0.0
        self.smoothed_box = None
        self.current_logged_for_this_item = False
