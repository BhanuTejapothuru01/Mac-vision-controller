# VisionMac 🖐️💻

**VisionMac** is a touchless macOS desktop controller powered by computer vision. It tracks your hand gestures via a standard webcam to seamlessly control mouse cursor movement, left clicks, right clicks, scrolling, and pause/resume states without needing a mouse or trackpad.

VisionMac operates **100% locally on device** with zero cloud latency, high-frequency frame tracking, and native Apple Silicon acceleration.

---

## 🖐️ Gesture Mapping Table

| Gesture | Hand Shape | macOS Action | Details |
| :--- | :--- | :--- | :--- |
| ☝️ **Point** | Index extended, others closed | **Move Mouse** | Smoothly moves cursor using index fingertip location |
| 🤏 **Pinch** | Thumb + Index tip touch | **Left Click** | Single debounced left mouse click |
| ✌️ **Two Finger** | Index + Middle extended | **Scroll** | Tracks vertical movement delta to scroll windows |
| ✊ **Fist** | All fingers closed | **Right Click** | Single debounced right mouse click (Unpauses system) |
| 🖐️ **Open Palm** | All 5 fingers extended | **Pause Control** | Freezes cursor & ignores inputs until unpaused |

---

## 🏗️ Architecture Overview

```
                          ┌──────────────────────────┐
                          │   Webcam Frame Capture   │
                          └─────────────┬────────────┘
                                        │ (BGR Frame)
                                        ▼
                          ┌──────────────────────────┐
                          │   Hand Tracker Module    │
                          │  (MediaPipe Tasks Vision) │
                          └─────────────┬────────────┘
                                        │ (21 Normalized Landmarks)
                                        ▼
                          ┌──────────────────────────┐
                          │    Gesture Recognizer    │
                          │(Geometric + Buffer Filter)│
                          └─────────────┬────────────┘
                                        │ (Stabilized Gesture + Confidence)
                                        ▼
┌──────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
│  Floating Status HUD     │<───│       Main Loop          │───>│   Action Engine Module   │
│  (Always-On-Top Tkinter) │    │   (Lifecycle & Safety)   │    │   (PyAutoGUI macOS API)  │
└──────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘
```

### Module Structure
- `main.py`: Main application loop orchestrating frame capture, tracking, action dispatch, safety checks, and HUD updates.
- `hand_tracker.py`: Wraps MediaPipe Tasks `HandLandmarker` for 21-point 2D/3D hand skeleton extraction and debug visualization.
- `gesture_recognizer.py`: Pure geometric finger classification engine featuring scale-invariant hand math and N-frame temporal buffer smoothing.
- `action_engine.py`: Translates recognized hand coordinates into macOS mouse movements with Exponential Moving Average (EMA) damping, dead-zone noise suppression, click debouncing, and vertical scroll delta calculation.
- `overlay_ui.py`: Always-on-top, non-intrusive floating glassmorphic Tkinter HUD showing live control state, active gesture, current action, and confidence score.
- `config.py`: Centralized configuration file for tuning smoothing factors, dead zones, margin padding, debounce timers, and dry-run mode.

---

## 🛠️ macOS System Permissions Setup

Because VisionMac automates cursor input and accesses the webcam, macOS security requires explicit user permissions:

### 1. Camera Permission
- When running `python main.py`, macOS will prompt for camera access. Click **Allow**.
- To grant manually, go to:
  `System Settings > Privacy & Security > Camera` ➔ Toggle **Terminal** (or **Antigravity IDE** / **Python**) **ON**.

### 2. Accessibility Permission (Required for Mouse Movement & Clicks)
- `pyautogui` requires Accessibility privileges to move the mouse pointer and click.
- Open: `System Settings > Privacy & Security > Accessibility`
- Click `+` and add **Terminal** (or your Python runtime application), then toggle it **ON**.

### 3. Screen Recording Permission
- Open: `System Settings > Privacy & Security > Screen & System Audio Recording`
- Ensure **Terminal** / **Python** is enabled if prompted by macOS.

---

## 🚀 Quickstart Guide

### Prerequisites
- macOS 12+ (Apple Silicon or Intel)
- Python 3.10 or higher
- Webcam

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/BhanuTejapothuru01/macvision-controller.git
cd "macvision controller"

# 2. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Run VisionMac
python main.py
```

Press **`Esc`** or **`q`** inside the camera window to stop the controller at any time.

---

## 🛡️ Safety Controls

- **Global Panic Key**: Pressing `Esc` or `q` immediately halts execution, releases the camera feed, and closes all overlay windows.
- **Auto-Pause Timeout**: If your hand leaves the camera frame for more than **2.0 seconds**, VisionMac automatically enters `🔴 PAUSED` state to prevent runaway cursor movements.
- **Dry-Run Mode**: Set `DRY_RUN_MODE = True` in `config.py` to log all actions to the console without physically executing mouse movements or clicks.

---

## ⚠️ Known Limitations

1. **Ambient Lighting**: Requires moderate lighting for MediaPipe to track landmarks accurately.
2. **Extreme Camera Angles**: Tracking is most responsive when the palm faces the camera directly.
3. **Multi-Monitor Setup**: Default coordinate scaling maps to the main primary display (`pyautogui.size()`).

---

## 🗺️ Future Roadmap

- [ ] **Voice Command Integration**: Combine gesture control with local Siri/Whisper voice triggers.
- [ ] **Azure Cloud Sync**: Sync custom gesture profiles across devices.
- [ ] **Custom Gesture Trainer**: GUI utility allowing users to record and train custom hand gestures.
- [ ] **Dual Hand Control**: Support left hand for modifier keys (Shift, Cmd) and right hand for cursor control.

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
