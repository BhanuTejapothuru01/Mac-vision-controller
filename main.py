"""
VisionMac - Main Entry Point
Ultra-Lightweight Touchless macOS Controller Loop
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
    print(" 🖐️ VisionMac - Ultra-Lightweight Controller Starting...")
    print("=" * 60)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera index {config.CAMERA_INDEX}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    tracker = HandTracker(max_hands=1)
    recognizer = GestureRecognizer(history_size=2)
    action_engine = ActionEngine(
        smoothing_alpha=config.SMOOTHING_ALPHA,
        dead_zone_px=config.DEAD_ZONE_PX,
        margin_x=config.MARGIN_X,
        margin_y=config.MARGIN_Y,
        dry_run=config.DRY_RUN_MODE
    )

    overlay = StatusOverlayUI() if config.USE_STATUS_OVERLAY else None

    print(f"[VisionMac] Active Display Bounds: {action_engine.screen_w}x{action_engine.screen_h}")
    print("[VisionMac] Show hand to control Mac. Press 'Esc' or 'q' to Quit.")

    prev_time = time.time()
    last_hand_seen_time = time.time()
    last_action_desc = "Move Hand to Control"
    frame_target_delay = 1.0 / config.TARGET_FPS

    try:
        while True:
            loop_start = time.time()

            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Camera frame capture failed.")
                break

            # Mirror frame horizontally
            frame = cv2.flip(frame, 1)

            # 1. Track Hand (using downsampled AI inference)
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

            # 4. Action Dispatch
            if hand_detected:
                if gesture == GESTURE_OPEN_PALM:
                    action_engine.is_paused = True
                    last_action_desc = "PAUSED (Open Palm)"
                else:
                    action_engine.is_paused = False

                if not action_engine.is_paused:
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

            cv2.putText(frame, f"VisionMac - {state_str}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, state_color, 2, cv2.LINE_AA)
            cv2.putText(frame, f"Gesture: {gesture_text}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Action: {last_action_desc}", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 215, 255), 1, cv2.LINE_AA)
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

            # FPS Governor: Paces loop execution to save CPU & battery
            elapsed = time.time() - loop_start
            sleep_needed = frame_target_delay - elapsed
            if sleep_needed > 0.001:
                time.sleep(sleep_needed)

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
