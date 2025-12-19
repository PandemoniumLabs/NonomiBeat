<div align="center">
    <img src="images/halo.png" alt="logo" />
    <br>
    <img src="https://img.shields.io/badge/version-0.0.1--alpha-FF69B4?style=for-the-badge" />
    <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Android-blue?style=for-the-badge" />
    <img src="https://img.shields.io/badge/license-GPL--3.0-green?style=for-the-badge"/>
</div>
<br>

**Adaptive LoFi generator.**\
A cross-platform, procedural LoFi generator that adapts your background audio in real-time. 

---

## Features

* **Procedural DSP** – Powered by `libpd`. Real-time Low-Pass filters and tape-wobble logic that work on Linux and Android.
* **Environment Aware** – 
    * **Linux:** Uses OpenCV to analyze room brightness and color temp.
    * **Android:** Uses the physical **Ambient Light Sensor** (ALS) 
* **Tiling-Aware (Hyprland)** – Deep integration with `hyprctl` to track active window classes and shift between audio profiles.
* **ASCII Visualizer** – A real-time video-to-ASCII aesthetic wrapper (optional/toggleable).
* **Privacy First** – Local-only processing. No snapshots saved, no telemetry, no cloud bullshit.

---

## Installation (Linux)

```bash
git clone https://github.com/XeonXE534/NonomiBeat.git
cd NonomiBeat

bash ./install.sh
```
---

## Installation (Android)

* WIP

---

## Requirements

| Platform | Dependencies                                   |
|----------|------------------------------------------------|
| Linux    | Arch/EndeavourOS, Hyprland, Python 3.10+       |
| Android  | Android 8.0+, Light Sensor                     |

> All packages/dependencies are installed via the `install.sh` script on Linux or bundled in the Android APK.
---

## Notes

* Arch First: Developed on EndeavourOS w/ Hyprland.
* Privacy: Android version uses the Light Sensor by default to avoid unnecessary camera permissions.

---

## License

GPL 3.0 – see LICENSE file for details

---

## Disclaimer

NonomiBeat is an independent, open-source project and is not affiliated with, endorsed, or sponsored by Nexon Games, Yostar, or Blue Archive.
The character Nonomi and related assets belong to Nexon Games Co., Ltd.
All character references are for fan and educational purposes only.

If you are a copyright holder and believe any content used here violates your rights, please open an issue or contact me — I'll remove it immediately.