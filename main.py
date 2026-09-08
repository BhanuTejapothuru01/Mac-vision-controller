"""
VisionMac - Main Entry Point
Phase 6: Full Integration with Floating Status HUD & Safety Controls
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
    GESTURE_POINT: "☝️ POINT",
    GESTURE_PINCH: "🤏 PINCH",
    GESTURE_TWO_FINGER: "✌️ TWO_FINGER",
    GESTURE_FIST: "✊ FIST",
    GESTURE_OPEN_PALM: "🖐️ OPEN_PALM",
    GESTURE_NONE: "❓ NONE"
}


def main():
    """Main VisionMac application loop."""
    print("[VisionMac] Starting VisionMac Touchless Controller...")
    cap = cv2.VideoCapture(config.CAMERA_INDEX)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera index {config.CAMERA_INDEX}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    tracker = HandTracker(max_hands=1)
    recognizer = GestureRecognizer(history_size=5)
    action_engine = ActionEngine(
        smoothing_alpha=config.SMOOTHING_ALPHA,
        dead_zone_px=config.DEAD_ZONE_PX,
        margin_x=config.MARGIN_X,
        margin_y=config.MARGIN_Y,
        dry_run=config.DRY_RUN_MODE
    )

    overlay = StatusOverlayUI() if config.USE_STATUS_OVERLAY else None

    print(f"[VisionMac] Initialization Complete.")
    print(f"[VisionMac] Display Resolution: {action_engine.screen_w}x{action_engine.screen_h}")
    print("[VisionMac] Press 'Esc' or 'q' to stop.")

    prev_time = time.time()
    last_hand_seen_time = time.time()
    last_action_desc = "System Initialized"

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Camera frame capture failed.")
                break

            # Mirror frame horizontally for intuitive self-view
            frame = cv2.flip(frame, 1)

            # 1. Track Hand
            normalized_lm, pixel_lm = tracker.process_frame(frame)
            hand_detected = len(pixel_lm) == 21

            # 2. Recognize Gesture
            gesture, confidence = recognizer.process(normalized_lm)

            # 3. Safety Auto-Pause Timeout Check
            now = time.time()
            if hand_detected:
                last_hand_seen_time = now
            else:
                if now - last_hand_seen_time > config.AUTO_PAUSE_TIMEOUT_SEC:
                    if not action_engine.is_paused:
                        action_engine.set_pause(True)
                        last_action_desc = "Auto-Paused (No Hand)"

            # 4. Action Execution
            if hand_detected:
                if gesture == GESTURE_OPEN_PALM:
                    action_engine.set_pause(True)
                    last_action_desc = "Control PAUSED"

                elif gesture in (GESTURE_FIST, GESTURE_PINCH) and action_engine.is_paused:
                    action_engine.set_pause(False)
                    last_action_desc = "Control RESUMED"

                elif not action_engine.is_paused:
                    if gesture == GESTURE_POINT:
                        index_tip = normalized_lm[8]
                        pos = action_engine.move_cursor(index_tip["x"], index_tip["y"])
                        last_action_desc = f"Move to {pos}"

                    elif gesture == GESTURE_PINCH:
                        clicked = action_engine.left_click()
                        if clicked:
                            last_action_desc = "Left Click"

                    elif gesture == GESTURE_FIST:
                        rclicked = action_engine.right_click()
                        if rclicked:
                            last_action_desc = "Right Click"

                    elif gesture == GESTURE_TWO_FINGER:
                        index_tip = normalized_lm[8]
                        middle_tip = normalized_lm[12]
                        mid_y = (index_tip["y"] + middle_tip["y"]) / 2.0
                        scrolled_clicks = action_engine.scroll(mid_y)
                        if scrolled_clicks != 0:
                            direction = "UP" if scrolled_clicks > 0 else "DOWN"
                            last_action_desc = f"Scroll {direction}"
                    else:
                        action_engine.reset_smoothing()
                else:
                    action_engine.reset_smoothing()
            else:
                action_engine.reset_smoothing()

            # 5. Draw Hand Overlay
            if hand_detected:
                frame = tracker.draw_landmarks(frame, pixel_lm)

            # Calculate FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-6)
            prev_time = curr_time

            # Render Camera HUD Text
            state_str = "🔴 PAUSED" if action_engine.is_paused else "🟢 ACTIVE"
            state_color = (0, 0, 255) if action_engine.is_paused else (0, 255, 0)
            gesture_text = GESTURE_EMOJI_MAP.get(gesture, gesture)

            cv2.putText(
                frame,
                f"VisionMac - {state_str}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                state_color,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Gesture: {gesture_text} ({int(confidence * 100)}%)",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Action: {last_action_desc}",
                (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 215, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"FPS: {fps:.1f} | Esc / q to Quit",
                (10, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (180, 180, 180),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow(config.WINDOW_NAME, frame)

            # Update Floating Tkinter Overlay Window
            if overlay is not None:
                overlay.update_status(
                    is_paused=action_engine.is_paused,
                    gesture_text=gesture_text,
                    action_text=last_action_desc,
                    confidence_pct=int(confidence * 100)
                )

            # Global Panic Key Check (Esc key code 27 or 'q' key code 113)
            key = cv2.waitKey(1) & 0xFF
            if key == config.EMERGENCY_QUIT_KEY or key == ord("q"):
                print("[VisionMac] Emergency exit key pressed. Stopping...")
                break

    except KeyboardInterrupt:
        print("[VisionMac] Keyboard interrupt received.")
    finally:
        if overlay is not None:
            overlay.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[VisionMac] Shutdown complete.")


if __name__ == "__main__":
    main()
