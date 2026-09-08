"""
VisionMac - Action Engine
Phase 5: Mouse Movement, Clicks, Scrolling & Pause State Control
"""

import time
import math
from typing import Tuple, Dict, Optional
import pyautogui

import config

# Disable PyAutoGUI default delay for real-time responsiveness
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))


class ActionEngine:
    def __init__(
        self,
        smoothing_alpha: float = config.SMOOTHING_ALPHA,
        dead_zone_px: float = config.DEAD_ZONE_PX,
        margin_x: float = config.MARGIN_X,
        margin_y: float = config.MARGIN_Y,
        dry_run: bool = config.DRY_RUN_MODE
    ):
        """
        Initializes ActionEngine for full macOS interaction.
        """
        self.smoothing_alpha = smoothing_alpha
        self.dead_zone_px = dead_zone_px
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.dry_run = dry_run

        # macOS Screen Resolution
        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception:
            self.screen_w, self.screen_h = 1920, 1080

        # State tracking for EMA smoothing
        self.prev_screen_x: Optional[float] = None
        self.prev_screen_y: Optional[float] = None

        # State tracking for Scroll
        self.prev_scroll_mid_y: Optional[float] = None

        # Debounce timestamps
        self.last_left_click_time: float = 0.0
        self.last_right_click_time: float = 0.0
        self.last_pause_toggle_time: float = 0.0

        # Global Pause Flag
        self.is_paused: bool = False

    def map_camera_to_screen(self, norm_x: float, norm_y: float) -> Tuple[int, int]:
        """Maps normalized camera coordinates to screen pixel dimensions."""
        clamped_x = clamp(norm_x, self.margin_x, 1.0 - self.margin_x)
        clamped_y = clamp(norm_y, self.margin_y, 1.0 - self.margin_y)

        rel_x = (clamped_x - self.margin_x) / (1.0 - 2 * self.margin_x)
        rel_y = (clamped_y - self.margin_y) / (1.0 - 2 * self.margin_y)

        screen_x = int(rel_x * self.screen_w)
        screen_y = int(rel_y * self.screen_h)

        return screen_x, screen_y

    def move_cursor(self, norm_x: float, norm_y: float) -> Tuple[int, int]:
        """Calculates smoothed cursor position and moves mouse if active."""
        if self.is_paused:
            return int(self.prev_screen_x or 0), int(self.prev_screen_y or 0)

        raw_x, raw_y = self.map_camera_to_screen(norm_x, norm_y)

        if self.prev_screen_x is None or self.prev_screen_y is None:
            smooth_x = float(raw_x)
            smooth_y = float(raw_y)
        else:
            dist = math.sqrt((raw_x - self.prev_screen_x) ** 2 + (raw_y - self.prev_screen_y) ** 2)
            if dist < self.dead_zone_px:
                return int(self.prev_screen_x), int(self.prev_screen_y)

            smooth_x = self.smoothing_alpha * raw_x + (1.0 - self.smoothing_alpha) * self.prev_screen_x
            smooth_y = self.smoothing_alpha * raw_y + (1.0 - self.smoothing_alpha) * self.prev_screen_y

        target_x = int(round(smooth_x))
        target_y = int(round(smooth_y))

        if not self.dry_run:
            try:
                pyautogui.moveTo(target_x, target_y)
            except Exception as e:
                print(f"[ActionEngine Warning] moveTo failed: {e}")
        else:
            print(f"[DRY RUN] moveTo({target_x}, {target_y})")

        self.prev_screen_x = smooth_x
        self.prev_screen_y = smooth_y

        return target_x, target_y

    def left_click(self) -> bool:
        """Executes left click with debounce protection."""
        if self.is_paused:
            return False

        now = time.time()
        if now - self.last_left_click_time >= config.CLICK_DEBOUNCE_SEC:
            self.last_left_click_time = now
            if not self.dry_run:
                try:
                    pyautogui.click()
                except Exception as e:
                    print(f"[ActionEngine Warning] click failed: {e}")
            else:
                print("[DRY RUN] LEFT CLICK executed")
            return True
        return False

    def right_click(self) -> bool:
        """Executes right click with debounce protection."""
        if self.is_paused:
            return False

        now = time.time()
        if now - self.last_right_click_time >= config.RIGHT_CLICK_DEBOUNCE_SEC:
            self.last_right_click_time = now
            if not self.dry_run:
                try:
                    pyautogui.rightClick()
                except Exception as e:
                    print(f"[ActionEngine Warning] rightClick failed: {e}")
            else:
                print("[DRY RUN] RIGHT CLICK executed")
            return True
        return False

    def scroll(self, current_mid_y: float) -> int:
        """
        Translates vertical movement delta of two-finger midpoint into macOS scrolling.
        """
        if self.is_paused:
            self.prev_scroll_mid_y = None
            return 0

        if self.prev_scroll_mid_y is None:
            self.prev_scroll_mid_y = current_mid_y
            return 0

        delta_y = current_mid_y - self.prev_scroll_mid_y
        self.prev_scroll_mid_y = current_mid_y

        # Dead-zone threshold for micro vertical movement
        if abs(delta_y) < 0.005:
            return 0

        # Moving fingers UP (delta_y < 0) -> scroll UP (+clicks)
        # Moving fingers DOWN (delta_y > 0) -> scroll DOWN (-clicks)
        scroll_clicks = int(-delta_y * config.SCROLL_SENSITIVITY * 100.0)

        if scroll_clicks != 0:
            if not self.dry_run:
                try:
                    pyautogui.scroll(scroll_clicks)
                except Exception as e:
                    print(f"[ActionEngine Warning] scroll failed: {e}")
            else:
                print(f"[DRY RUN] SCROLL executed: {scroll_clicks} clicks")

        return scroll_clicks

    def set_pause(self, paused: bool) -> bool:
        """
        Sets global pause state with debounce protection.
        """
        now = time.time()
        if now - self.last_pause_toggle_time >= 0.80:
            if self.is_paused != paused:
                self.is_paused = paused
                self.last_pause_toggle_time = now
                print(f"[ActionEngine] Control state changed: {'PAUSED' if self.is_paused else 'ACTIVE'}")
                return True
        return False

    def reset_smoothing(self):
        """Resets transient tracking states."""
        self.prev_screen_x = None
        self.prev_screen_y = None
        self.prev_scroll_mid_y = None
