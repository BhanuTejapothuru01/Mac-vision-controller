"""
VisionMac - Action Engine
Direct Native macOS CoreGraphics (Quartz) OS Control Engine
"""

import time
import math
from typing import Tuple, Optional

# Attempt native macOS Quartz CoreGraphics import
HAS_QUARTZ = False
try:
    import Quartz.CoreGraphics as CG
    HAS_QUARTZ = True
except Exception:
    HAS_QUARTZ = False

import pyautogui
import config

# Disable PyAutoGUI default delay
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = False


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))


class ActionEngine:
    def __init__(
        self,
        smoothing_alpha: float = 0.40,
        dead_zone_px: float = 2.0,
        margin_x: float = 0.08,
        margin_y: float = 0.08,
        dry_run: bool = config.DRY_RUN_MODE
    ):
        """
        Initializes ActionEngine with Native macOS Quartz acceleration.
        """
        self.smoothing_alpha = smoothing_alpha
        self.dead_zone_px = dead_zone_px
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.dry_run = dry_run

        # Query display dimensions
        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception:
            self.screen_w, self.screen_h = 1470, 956

        print(f"[ActionEngine] Native Quartz Driver Active: {HAS_QUARTZ} (Display: {self.screen_w}x{self.screen_h})")

        # Position tracking for EMA smoothing
        self.prev_screen_x: Optional[float] = None
        self.prev_screen_y: Optional[float] = None

        # Scroll midpoint tracking
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
        """Moves macOS system cursor using native Quartz kernel calls."""
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

        target_x = float(round(smooth_x))
        target_y = float(round(smooth_y))

        if not self.dry_run:
            if HAS_QUARTZ:
                CG.CGWarpMouseCursorPosition((target_x, target_y))
            else:
                pyautogui.moveTo(int(target_x), int(target_y), _pause=False)
        else:
            print(f"[DRY RUN] moveTo({target_x}, {target_y})")

        self.prev_screen_x = smooth_x
        self.prev_screen_y = smooth_y

        return int(target_x), int(target_y)

    def left_click(self) -> bool:
        """Executes native macOS left click with debounce protection."""
        if self.is_paused:
            return False

        now = time.time()
        if now - self.last_left_click_time >= config.CLICK_DEBOUNCE_SEC:
            self.last_left_click_time = now
            if not self.dry_run:
                if HAS_QUARTZ:
                    point = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    down = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseDown, point, CG.kCGMouseButtonLeft)
                    up = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseUp, point, CG.kCGMouseButtonLeft)
                    CG.CGEventPost(CG.kCGHIDEventTap, down)
                    time.sleep(0.01)
                    CG.CGEventPost(CG.kCGHIDEventTap, up)
                else:
                    pyautogui.click(_pause=False)
                print("[VisionMac] Native Left Click Executed")
            else:
                print("[DRY RUN] LEFT CLICK executed")
            return True
        return False

    def right_click(self) -> bool:
        """Executes native macOS right click with debounce protection."""
        if self.is_paused:
            return False

        now = time.time()
        if now - self.last_right_click_time >= config.RIGHT_CLICK_DEBOUNCE_SEC:
            self.last_right_click_time = now
            if not self.dry_run:
                if HAS_QUARTZ:
                    point = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    down = CG.CGEventCreateMouseEvent(None, CG.kCGEventRightMouseDown, point, CG.kCGMouseButtonRight)
                    up = CG.CGEventCreateMouseEvent(None, CG.kCGEventRightMouseUp, point, CG.kCGMouseButtonRight)
                    CG.CGEventPost(CG.kCGHIDEventTap, down)
                    time.sleep(0.01)
                    CG.CGEventPost(CG.kCGHIDEventTap, up)
                else:
                    pyautogui.rightClick(_pause=False)
                print("[VisionMac] Native Right Click Executed")
            else:
                print("[DRY RUN] RIGHT CLICK executed")
            return True
        return False

    def scroll(self, current_mid_y: float) -> int:
        """Translates vertical movement delta into native macOS scrolling."""
        if self.is_paused:
            self.prev_scroll_mid_y = None
            return 0

        if self.prev_scroll_mid_y is None:
            self.prev_scroll_mid_y = current_mid_y
            return 0

        delta_y = current_mid_y - self.prev_scroll_mid_y
        self.prev_scroll_mid_y = current_mid_y

        if abs(delta_y) < 0.003:
            return 0

        scroll_units = int(-delta_y * 120.0)

        if scroll_units != 0:
            if not self.dry_run:
                if HAS_QUARTZ:
                    event = CG.CGEventCreateScrollWheelEvent(None, CG.kCGScrollEventUnitPixel, 1, scroll_units * 5)
                    CG.CGEventPost(CG.kCGHIDEventTap, event)
                else:
                    pyautogui.scroll(scroll_units, _pause=False)
            else:
                print(f"[DRY RUN] SCROLL executed: {scroll_units} units")

        return scroll_units

    def set_pause(self, paused: bool) -> bool:
        """Sets global pause state."""
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
