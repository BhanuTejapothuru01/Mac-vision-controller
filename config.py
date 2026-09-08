"""
VisionMac - Lightweight Configuration Settings
"""

import os

# Camera Capture Configuration
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30  # FPS governor for low CPU utilization

# AI Inference Downsampling (4x faster processing & lower memory footprint)
INFERENCE_WIDTH = 320
INFERENCE_HEIGHT = 240

# Debug and UI Configuration
WINDOW_NAME = "VisionMac - Live Feed"
SHOW_CAMERA_WINDOW = True
USE_STATUS_OVERLAY = True  # Lightweight Tkinter HUD

# Control & Action Engine Configuration
DRY_RUN_MODE = False

# Safety Controls
AUTO_PAUSE_TIMEOUT_SEC = 2.0  # Auto-pause if hand leaves frame for > 2.0s
EMERGENCY_QUIT_KEY = 27       # Esc key code in OpenCV

# Mouse Movement Tuning
SMOOTHING_ALPHA = 0.40  # Fast response
DEAD_ZONE_PX = 2.0      # Low threshold
MARGIN_X = 0.08          # 8% border
MARGIN_Y = 0.08

# Gesture Debounce Timers (Seconds)
CLICK_DEBOUNCE_SEC = 0.40
RIGHT_CLICK_DEBOUNCE_SEC = 0.55
SCROLL_SENSITIVITY = 12.0
