"""
VisionMac - Diagnostic & System Test Tool
"""

import time
import sys
import pyautogui
import cv2
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer, GESTURE_POINT
from action_engine import ActionEngine


def run_diagnostics():
    print("=" * 60)
    print(" 🛠️  VisionMac System & Hardware Diagnostic Tool")
    print("=" * 60)

    # 1. Test PyAutoGUI Screen Size
    try:
        w, h = pyautogui.size()
        print(f"[TEST 1/4] Screen Resolution Query: SUCCESS ({w}x{h})")
    except Exception as e:
        print(f"[TEST 1/4] Screen Resolution Query: FAILED ({e})")
        sys.exit(1)

    # 2. Test Mouse Automation
    print("\n[TEST 2/4] PyAutoGUI Mouse Movement Test:")
    print("  -> Moving cursor to (200, 200) in 1 second...")
    time.sleep(1.0)
    try:
        pyautogui.moveTo(200, 200, _pause=False)
        pos1 = pyautogui.position()
        print(f"  -> Mouse moved to: {pos1}")

        time.sleep(0.5)
        pyautogui.moveTo(700, 400, _pause=False)
        pos2 = pyautogui.position()
        print(f"  -> Mouse moved to: {pos2}")
        print("  [TEST 2/4] Mouse Automation: SUCCESS")
    except Exception as e:
        print(f"  [TEST 2/4] Mouse Automation: FAILED ({e})")
        print("  -> Please check macOS System Settings > Privacy & Security > Accessibility!")

    # 3. Test Camera Capture
    print("\n[TEST 3/4] Camera Hardware Access Test:")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  [TEST 3/4] Camera Access: FAILED (Could not open video stream)")
        print("  -> Please check macOS System Settings > Privacy & Security > Camera!")
        sys.exit(1)

    ret, frame = cap.read()
    if ret:
        h, w, _ = frame.shape
        print(f"  [TEST 3/4] Camera Access: SUCCESS (Captured frame {w}x{h})")
    else:
        print("  [TEST 3/4] Camera Access: FAILED (Empty frame)")
    cap.release()

    # 4. Test Hand Tracker & Gesture Recognizer
    print("\n[TEST 4/4] Hand Tracker & Model Asset Test:")
    try:
        tracker = HandTracker()
        recognizer = GestureRecognizer()
        print("  [TEST 4/4] MediaPipe Model Load: SUCCESS")
    except Exception as e:
        print(f"  [TEST 4/4] MediaPipe Model Load: FAILED ({e})")

    print("\n" + "=" * 60)
    print(" 🎉 All Diagnostic Tests Completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_diagnostics()
