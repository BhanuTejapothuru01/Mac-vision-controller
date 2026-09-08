"""
VisionMac - Main Entry Point
Ultra-Responsive Hand & Cursor Control System
"""

import time
import sys
import cv2
import config
from hand_tracker import HandTracker
from gesture_recognizer import (
    GestureRecognizer, GESTURE_NONE, GESTURE_POINT,
    GESTURE_PINCH, GESTURE_TWO_FINGER, GESTURE_FIST, GESTURE_OPEN_PALM
)
from action_engine import ActionEngine
from overlay_ui import StatusOverlayUI

GESTURE_EMOJI_MAP = {
    GESTURE_POINT: "☝️ POINT (Move Mouse)",
    GESTURE_PINCH: "🤏 PINCH (Left Click)",
    GESTURE_TWO_FINGER: "✌️ TWO_FINGER (Scroll)",
    GESTURE_FIST: "✊ FIST (Right Click)",
    GESTURE_OPEN_PALM: "🖐️ OPEN_PALM (Pause)",
    GESTURE_NONE: "🖐️ TRACKING (Move Mouse)"
}


def main():
    print("=" * 60)
    print(" 🖐️ VisionMac - macOS Touchless Controller Starting...")
    print("=" * 60)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera index {config.CAMERA_INDEX}.")
        print("Please check macOS System Settings > Privacy & Security > Camera.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    tracker = HandTracker(max_hands=1)
    recognizer = GestureRecognizer(history_size=2)  # Fast 2-frame response
    action_engine = ActionEngine(
        smoothing_alpha=0.40,  # Fast & smooth tracking
        dead_zone_px=2.0,      # Minimal dead zone for high sensitivity
        margin_x=0.08,          # Wide 8% active area
        margin_y=0.08,
        dry_run=config.DRY_RUN_MODE
    )

    overlay = StatusOverlayUI() if config.USE_STATUS_OVERLAY else None

    print(f"[VisionMac] Active Display Bounds: {action_engine.screen_w}x{action_engine.screen_h}")
    print("[VisionMac] Show hand to move mouse. Press 'Esc' or 'q' to Quit.")

    prev_time = time.time()
    last_hand_seen_time = time.time()
    last_action_desc = "Move Hand to Control"

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Camera frame capture failed.")
                break

            # Mirror frame horizontally for natural self-view
            frame = cv2.flip(frame, 1)

            # 1. Track Hand
            normalized_lm, pixel_lm = tracker.process_frame(frame)
            hand_detected = len(pixel_lm) == 21

            # 2. Recognize Gesture
            gesture, confidence = recognizer.process(normalized_lm)

            # 3. Safety Auto-Pause Check
            now = time.time()
            if hand_detected:
                last_hand_seen_time = now
            else:
                if now - last_hand_seen_time > config.AUTO_PAUSE_TIMEOUT_SEC:
                    action_engine.is_paused = True
                    last_action_desc = "Auto-Paused (No Hand)"

            # 4. Action Execution
            if hand_detected:
                # If open palm shown, toggle pause
                if gesture == GESTURE_OPEN_PALM:
                    action_engine.is_paused = True
                    last_action_desc = "PAUSED (Open Palm)"
                elif gesture == GESTURE_OPEN_PALM:
                    pass
                else:
                    # Unpause automatically whenever hand is moving or gesturing
                    action_engine.is_paused = False

                if not action_engine.is_paused:
                    # Action Dispatch
                    if gesture == GESTURE_PINCH:
                        clicked = action_engine.left_click()
                        last_action_desc = "Left Click" if clicked else "Pinch Held"

                    elif gesture == GESTURE_FIST:
                        rclicked = action_engine.right_click()
                        last_action_desc = "Right Click" if rclicked else "Fist Held"

                    elif gesture == GESTURE_TWO_FINGER:
                        index_tip = normalized_lm[8]
                        middle_tip = normalized_lm[12]
                        mid_y = (index_tip["y"] + middle_tip["y"]) / 2.0
                        scrolled_clicks = action_engine.scroll(mid_y)
                        if scrolled_clicks != 0:
                            direction = "UP" if scrolled_clicks > 0 else "DOWN"
                            last_action_desc = f"Scroll {direction}"
                        else:
                            last_action_desc = "Scrolling..."
                    else:
                        # DEFAULT: Track index fingertip (landmark 8) directly to cursor
                        index_tip = normalized_lm[8]
                        pos = action_engine.move_cursor(index_tip["x"], index_tip["y"])
                        last_action_desc = f"Moving Cursor {pos}"
            else:
                action_engine.reset_smoothing()

            # 5. Draw Hand Skeleton Overlay
            if hand_detected:
                frame = tracker.draw_landmarks(frame, pixel_lm)

            # Calculate FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-6)
            prev_time = curr_time

            # Render Camera Feed HUD Text
            state_str = "🔴 PAUSED" if action_engine.is_paused else "🟢 ACTIVE"
            state_color = (0, 0, 255) if action_engine.is_paused else (0, 255, 0)
            gesture_text = GESTURE_EMOJI_MAP.get(gesture, "🖐️ TRACKING")

            cv2.putText(frame, f"VisionMac - {state_str}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2, cv2.LINE_AA)
            cv2.putText(frame, f"Gesture: {gesture_text}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Action: {last_action_desc}", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 215, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {fps:.1f} | Esc/q to Quit", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1, cv2.LINE_AA)

            cv2.imshow(config.WINDOW_NAME, frame)

            # Update Floating Tkinter Overlay Window
            if overlay is not None:
                overlay.update_status(
                    is_paused=action_engine.is_paused,
                    gesture_text=gesture_text,
                    action_text=last_action_desc,
                    confidence_pct=int(confidence * 100) if hand_detected else 0
                )

            # Emergency Exit Check
            key = cv2.waitKey(1) & 0xFF
            if key == config.EMERGENCY_QUIT_KEY or key == ord("q"):
                print("[VisionMac] Stopping...")
                break

    except KeyboardInterrupt:
        print("[VisionMac] Interrupted.")
    finally:
        if overlay is not None:
            overlay.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[VisionMac] Stopped.")


if __name__ == "__main__":
    main()
