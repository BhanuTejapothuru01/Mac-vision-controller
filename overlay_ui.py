"""
VisionMac - Floating Status Overlay UI
Phase 6: Always-On-Top Glassmorphic Tkinter HUD
"""

import tkinter as tk
from typing import Optional


class StatusOverlayUI:
    def __init__(self, width: int = 240, height: int = 150):
        """
        Initializes a floating always-on-top status HUD window using Tkinter.
        """
        self.root = tk.Tk()
        self.root.title("VisionMac")
        self.root.geometry(f"{width}x{height}+40+40")  # Top-left screen placement
        self.root.resizable(False, False)

        # macOS Floating Window Attributes
        self.root.wm_attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", 0.92)  # Semi-transparent HUD background
        except Exception:
            pass

        # Dark Glassmorphic Color Palette
        self.bg_color = "#181825"
        self.card_bg = "#1e1e2e"
        self.text_primary = "#cdd6f4"
        self.text_secondary = "#a6adc8"
        self.active_color = "#a6e3a1"
        self.paused_color = "#f38ba8"
        self.accent_color = "#89b4fa"

        self.root.configure(bg=self.bg_color)

        # Main Container Frame
        self.container = tk.Frame(self.root, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground="#313244")
        self.container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Title Header
        self.lbl_title = tk.Label(
            self.container,
            text="VisionMac Controller",
            font=("Helvetica", 11, "bold"),
            fg=self.accent_color,
            bg=self.card_bg
        )
        self.lbl_title.pack(anchor="w", padx=10, pady=(6, 2))

        # Status Badge (ACTIVE / PAUSED)
        self.lbl_status = tk.Label(
            self.container,
            text="🟢 ACTIVE",
            font=("Helvetica", 10, "bold"),
            fg=self.active_color,
            bg=self.card_bg
        )
        self.lbl_status.pack(anchor="w", padx=10, pady=1)

        # Gesture Label
        self.lbl_gesture = tk.Label(
            self.container,
            text="Gesture: None",
            font=("Helvetica", 9),
            fg=self.text_primary,
            bg=self.card_bg
        )
        self.lbl_gesture.pack(anchor="w", padx=10, pady=1)

        # Action Label
        self.lbl_action = tk.Label(
            self.container,
            text="Action: Idle",
            font=("Helvetica", 9),
            fg=self.text_secondary,
            bg=self.card_bg
        )
        self.lbl_action.pack(anchor="w", padx=10, pady=1)

        # Confidence Label
        self.lbl_confidence = tk.Label(
            self.container,
            text="Confidence: 0%",
            font=("Helvetica", 8, "italic"),
            fg="#89dceb",
            bg=self.card_bg
        )
        self.lbl_confidence.pack(anchor="w", padx=10, pady=(1, 6))

    def update_status(self, is_paused: bool, gesture_text: str, action_text: str, confidence_pct: int):
        """
        Updates the HUD labels live. Thread-safe when called within main event loop or via root.update().
        """
        if is_paused:
            self.lbl_status.config(text="🔴 PAUSED", fg=self.paused_color)
        else:
            self.lbl_status.config(text="🟢 ACTIVE", fg=self.active_color)

        self.lbl_gesture.config(text=f"Gesture: {gesture_text}")
        self.lbl_action.config(text=f"Action: {action_text}")
        self.lbl_confidence.config(text=f"Confidence: {confidence_pct}%")

        # Process pending Tkinter UI events
        try:
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def close(self):
        """Destroys the overlay window."""
        try:
            self.root.destroy()
        except Exception:
            pass
