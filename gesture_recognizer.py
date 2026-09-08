"""
VisionMac - Gesture Recognition Engine
Phase 3: Geometric Classification & Temporal Smoothing
"""

import math
from collections import deque
from typing import List, Dict, Tuple


# Gesture Enum Constants
GESTURE_NONE = "NONE"
GESTURE_POINT = "POINT"
GESTURE_PINCH = "PINCH"
GESTURE_TWO_FINGER = "TWO_FINGER"
GESTURE_FIST = "FIST"
GESTURE_OPEN_PALM = "OPEN_PALM"


def euclidean_distance(p1: Dict[str, float], p2: Dict[str, float]) -> float:
    """Calculates 2D/3D Euclidean distance between two landmark points."""
    return math.sqrt(
        (p1["x"] - p2["x"]) ** 2 +
        (p1["y"] - p2["y"]) ** 2 +
        (p1.get("z", 0.0) - p2.get("z", 0.0)) ** 2
    )


class GestureRecognizer:
    def __init__(self, history_size: int = 5, min_confidence: float = 0.5):
        """
        Initializes GestureRecognizer with temporal smoothing buffer.
        """
        self.history_size = history_size
        self.min_confidence = min_confidence
        self.gesture_history = deque(maxlen=history_size)
        self.last_stable_gesture = GESTURE_NONE

    def recognize_frame_gesture(self, landmarks: List[Dict[str, float]]) -> Tuple[str, float]:
        """
        Pure geometric classification function.
        Takes 21 normalized hand landmarks and returns (raw_gesture, confidence).
        """
        if not landmarks or len(landmarks) < 21:
            return GESTURE_NONE, 0.0

        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]

        index_tip = landmarks[8]
        index_pip = landmarks[6]
        index_mcp = landmarks[5]

        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        middle_mcp = landmarks[9]

        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        ring_mcp = landmarks[13]

        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]
        pinky_mcp = landmarks[17]

        # Calculate hand scale (distance from wrist to middle MCP) for scale invariance
        hand_scale = euclidean_distance(wrist, middle_mcp)
        if hand_scale < 1e-4:
            return GESTURE_NONE, 0.0

        # Helper: test if finger is extended (distance from wrist to tip > distance from wrist to PIP * 1.08)
        index_ext = euclidean_distance(wrist, index_tip) > (euclidean_distance(wrist, index_pip) * 1.08)
        middle_ext = euclidean_distance(wrist, middle_tip) > (euclidean_distance(wrist, middle_pip) * 1.08)
        ring_ext = euclidean_distance(wrist, ring_tip) > (euclidean_distance(wrist, ring_pip) * 1.08)
        pinky_ext = euclidean_distance(wrist, pinky_tip) > (euclidean_distance(wrist, pinky_pip) * 1.08)

        # Thumb extension: tip far from index MCP or pinky MCP
        thumb_dist_pinky_mcp = euclidean_distance(thumb_tip, pinky_mcp)
        thumb_ext = (thumb_dist_pinky_mcp / hand_scale) > 0.80

        # 1. OPEN PALM Gesture (🖐️) - All 5 fingers extended
        if index_ext and middle_ext and ring_ext and pinky_ext and thumb_ext:
            confidence = 0.95
            return GESTURE_OPEN_PALM, confidence

        # 2. FIST Gesture (✊) - All 4 main fingers folded
        if not index_ext and not middle_ext and not ring_ext and not pinky_ext:
            confidence = 0.95
            return GESTURE_FIST, confidence

        # 3. PINCH Gesture (🤏) - Thumb tip and Index tip touching
        pinch_dist = euclidean_distance(thumb_tip, index_tip) / hand_scale
        pinch_threshold = 0.35  # Normalized touch threshold
        if pinch_dist < pinch_threshold and (index_ext or euclidean_distance(wrist, index_tip) > euclidean_distance(wrist, index_mcp)):
            confidence = max(0.5, 1.0 - (pinch_dist / pinch_threshold) * 0.5)
            return GESTURE_PINCH, round(confidence, 2)

        # 4. TWO_FINGER Gesture (✌️) - Index & Middle extended, Ring & Pinky folded
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            two_finger_dist = euclidean_distance(index_tip, middle_tip) / hand_scale
            confidence = 0.90 if two_finger_dist < 0.6 else 0.75
            return GESTURE_TWO_FINGER, confidence

        # 5. POINT Gesture (☝️) - Index extended, Middle, Ring & Pinky folded
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            confidence = 0.90
            return GESTURE_POINT, confidence

        # Fallback / Transition states
        return GESTURE_NONE, 0.30

    def process(self, landmarks: List[Dict[str, float]]) -> Tuple[str, float]:
        """
        Processes frame landmarks, applies temporal smoothing buffer,
        and returns stabilized (gesture, confidence).
        """
        raw_gesture, confidence = self.recognize_frame_gesture(landmarks)

        if len(landmarks) < 21 or raw_gesture == GESTURE_NONE:
            self.gesture_history.append(GESTURE_NONE)
            return GESTURE_NONE, 0.0

        self.gesture_history.append(raw_gesture)

        # Count occurrences in history buffer
        counts: Dict[str, int] = {}
        for g in self.gesture_history:
            counts[g] = counts.get(g, 0) + 1

        most_common_gesture, max_count = max(counts.items(), key=lambda item: item[1])

        # Require majority agreement in history buffer
        if max_count >= (self.history_size // 2 + 1):
            self.last_stable_gesture = most_common_gesture
            return most_common_gesture, confidence
        else:
            return self.last_stable_gesture, round(confidence * 0.8, 2)
