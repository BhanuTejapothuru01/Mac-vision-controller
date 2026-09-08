"""
VisionMac - Ultra-Lightweight Hand Tracking Module
Phase 2: Optimized MediaPipe Hand Tracker Wrapper
"""

import os
import ssl
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions
import config

# Hand Landmark Connections (21 connections)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm Base
]

MODEL_FILENAME = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


def ensure_model_exists(model_path: str = MODEL_FILENAME) -> str:
    """Ensures the MediaPipe hand landmarker task model file is present locally."""
    if not os.path.exists(model_path):
        print(f"[HandTracker] Downloading lightweight model asset to {model_path}...")
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(MODEL_URL, context=context) as resp, open(model_path, "wb") as out:
            out.write(resp.read())
        print("[HandTracker] Model downloaded successfully.")
    return model_path


class HandTracker:
    def __init__(self, max_hands: int = 1, min_detection_confidence: float = 0.5):
        """Initializes MediaPipe HandLandmarker with fast CPU/Metal delegate."""
        model_path = ensure_model_exists()
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence,
            running_mode=vision.RunningMode.IMAGE,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: np.ndarray):
        """
        Processes image frame using downsampled AI inference for ultra-low latency & CPU usage.

        Returns:
            normalized_landmarks: list of 21 dicts [{'x': float, 'y': float, 'z': float}, ...] or []
            pixel_landmarks: list of 21 tuples [(x_px, y_px), ...] scaled to frame resolution
        """
        orig_h, orig_w, _ = frame_bgr.shape

        # Downsample frame for 4x faster MediaPipe AI inference
        small_frame = cv2.resize(frame_bgr, (config.INFERENCE_WIDTH, config.INFERENCE_HEIGHT), interpolation=cv2.INTER_NEAREST)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)

        detection_result = self.landmarker.detect(mp_image)

        if not detection_result.hand_landmarks:
            return [], []

        primary_hand = detection_result.hand_landmarks[0]

        normalized_landmarks = []
        pixel_landmarks = []

        for lm in primary_hand:
            normalized_landmarks.append({"x": lm.x, "y": lm.y, "z": lm.z})
            px = int(clamp(lm.x, 0.0, 1.0) * orig_w)
            py = int(clamp(lm.y, 0.0, 1.0) * orig_h)
            pixel_landmarks.append((px, py))

        return normalized_landmarks, pixel_landmarks

    def draw_landmarks(self, frame_bgr: np.ndarray, pixel_landmarks: list) -> np.ndarray:
        """Draws visual debug skeleton lines and joint points on frame."""
        if not pixel_landmarks:
            return frame_bgr

        for start_idx, end_idx in HAND_CONNECTIONS:
            pt1 = pixel_landmarks[start_idx]
            pt2 = pixel_landmarks[end_idx]
            cv2.line(frame_bgr, pt1, pt2, (0, 215, 255), 2, cv2.LINE_AA)

        for idx, (px, py) in enumerate(pixel_landmarks):
            if idx == 8:
                cv2.circle(frame_bgr, (px, py), 7, (0, 255, 0), -1, cv2.LINE_AA)
            elif idx == 4:
                cv2.circle(frame_bgr, (px, py), 6, (255, 0, 255), -1, cv2.LINE_AA)
            else:
                cv2.circle(frame_bgr, (px, py), 3, (0, 165, 255), -1, cv2.LINE_AA)

        return frame_bgr


def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))
