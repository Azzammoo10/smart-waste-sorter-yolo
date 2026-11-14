"""Camera capture module using OpenCV with Windows DirectShow optimizations."""
from __future__ import annotations

import platform

import cv2
import numpy as np


class CameraManager:
    """Manages OpenCV VideoCapture with proper resource cleanup."""

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None

    def start(self) -> bool:
        """Open camera using CAP_DSHOW on Windows for fast startup."""
        if self._cap is not None and self._cap.isOpened():
            return True

        if platform.system() == "Windows":
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            # Fallback to default backend
            self._cap = cv2.VideoCapture(self.camera_index)

        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, 30)
            return True
        return False

    def read_frame(self) -> tuple[bool, np.ndarray | None]:
        """Read a single frame from the camera."""
        if self._cap is None or not self._cap.isOpened():
            return False, None
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return False, None
        return True, frame

    def release(self) -> None:
        """Release the camera hardware cleanly."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> CameraManager:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    @staticmethod
    def get_available_cameras(max_tested: int = 3) -> list[int]:
        """Test and return a list of accessible camera indices."""
        available: list[int] = []
        for index in range(max_tested):
            backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                available.append(index)
                cap.release()
        return available

