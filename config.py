"""
VisionMac - Configuration Settings
"""

import os

# Camera Configuration
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS_TARGET = 30

# Debug and UI Configuration
WINDOW_NAME = "VisionMac - Camera Feed"
SHOW_DEBUG_OVERLAY = True
USE_STATUS_OVERLAY = True  # Enable Tkinter floating status window HUD

# Control & Action Engine Configuration
DRY_RUN_MODE = False  # Set to True to log mouse actions without moving real system cursor

# Safety Controls
AUTO_PAUSE_TIMEOUT_SEC = 2.0  # Auto-pause control if no hand is detected for > 2.0s
EMERGENCY_QUIT_KEY = 27       # Esc key code in OpenCV (also 'q' key supported)

# Mouse Movement Tuning
SMOOTHING_ALPHA = 0.25  # EMA weight: lower = smoother, higher = faster response
DEAD_ZONE_PX = 4.0      # Ignore movement deltas smaller than 4 pixels to prevent tremor jitter
MARGIN_X = 0.12         # Active interaction padding (12% horizontal border)
MARGIN_Y = 0.12         # Active interaction padding (12% vertical border)

# Gesture Debounce Timers (Seconds)
CLICK_DEBOUNCE_SEC = 0.45
RIGHT_CLICK_DEBOUNCE_SEC = 0.60
SCROLL_SENSITIVITY = 15.0  # Scroll step multiplier
