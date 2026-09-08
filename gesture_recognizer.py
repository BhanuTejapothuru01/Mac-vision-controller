"""
VisionMac - Gesture Recognition Engine
Phase 3: Robust Geometric Classification & Responsive Smoothing
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
    def __init__(self, history_size: int = 3, min_confidence: float = 0.5):
        """
        Initializes GestureRecognizer with responsive temporal smoothing buffer.
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

        # Calculate hand scale (distance from wrist to middle MCP)
        hand_scale = euclidean_distance(wrist, middle_mcp)
        if hand_scale < 1e-4:
            return GESTURE_NONE, 0.0

        # Finger distances from wrist
        d_wrist_index_tip = euclidean_distance(wrist, index_tip)
        d_wrist_index_pip = euclidean_distance(wrist, index_pip)

        d_wrist_middle_tip = euclidean_distance(wrist, middle_tip)
        d_wrist_middle_pip = euclidean_distance(wrist, middle_pip)

        d_wrist_ring_tip = euclidean_distance(wrist, ring_tip)
        d_wrist_ring_pip = euclidean_distance(wrist, ring_pip)

        d_wrist_pinky_tip = euclidean_distance(wrist, pinky_tip)
        d_wrist_pinky_pip = euclidean_distance(wrist, pinky_pip)

        # Forgiving extension test (distance from wrist to tip > distance from wrist to PIP)
        index_ext = d_wrist_index_tip > (d_wrist_index_pip * 1.01)
        middle_ext = d_wrist_middle_tip > (d_wrist_middle_pip * 1.01)
        ring_ext = d_wrist_ring_tip > (d_wrist_ring_pip * 1.01)
        pinky_ext = d_wrist_pinky_tip > (d_wrist_pinky_pip * 1.01)

        # Thumb extension: tip far from pinky MCP
        thumb_dist_pinky_mcp = euclidean_distance(thumb_tip, pinky_mcp)
        thumb_ext = (thumb_dist_pinky_mcp / hand_scale) > 0.75

        # Pinch detection: distance between thumb tip & index tip
        pinch_dist = euclidean_distance(thumb_tip, index_tip) / hand_scale
        pinch_threshold = 0.40

        # 1. OPEN PALM Gesture (🖐️) - All 5 fingers extended
        if index_ext and middle_ext and ring_ext and pinky_ext and thumb_ext:
            return GESTURE_OPEN_PALM, 0.95

        # 2. FIST Gesture (✊) - All 4 main fingers folded
        if not index_ext and not middle_ext and not ring_ext and not pinky_ext:
            return GESTURE_FIST, 0.95

        # 3. PINCH Gesture (🤏) - Thumb tip & Index tip close
        if pinch_dist < pinch_threshold and (index_ext or d_wrist_index_tip > d_wrist_index_mcp):
            confidence = max(0.5, 1.0 - (pinch_dist / pinch_threshold) * 0.5)
            return GESTURE_PINCH, round(confidence, 2)

        # 4. TWO_FINGER Gesture (✌️) - Index & Middle extended, Ring & Pinky folded
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            two_finger_dist = euclidean_distance(index_tip, middle_tip) / hand_scale
            confidence = 0.90 if two_finger_dist < 0.7 else 0.75
            return GESTURE_TWO_FINGER, confidence

        # 5. POINT Gesture (☝️) - Index extended, Middle folded (or Index tip significantly further than Middle tip)
        if index_ext and (not middle_ext or d_wrist_index_tip > d_wrist_middle_tip * 1.15):
            return GESTURE_POINT, 0.90

        # Primary Fallback: If index is extended and no other fingers are clearly active, default to POINT
        if index_ext:
            return GESTURE_POINT, 0.80

        return GESTURE_NONE, 0.30

    def process(self, landmarks: List[Dict[str, float]]) -> Tuple[str, float]:
        """
        Processes frame landmarks with responsive temporal buffer.
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

        if max_count >= (self.history_size // 2 + 1):
            self.last_stable_gesture = most_common_gesture
            return most_common_gesture, confidence
        else:
            return raw_gesture, confidence
