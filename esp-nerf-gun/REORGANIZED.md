# 🎯 ESP WiFi Nerf Gun Controller - Reorganized Project

## ✅ **Project Successfully Reorganized!**

Your project has been moved from two messy folders into one clean, organized structure:

### **OLD Structure** ❌
```
ESP_test/                           (PlatformIO project with .venv)
250722-190354-esp8266-nonos-sdk-blink/  (Actual nerf gun code)
```

### **NEW Structure** ✅
```
ESP_WIFI_NERF/                     (Single organized project)
├── .venv/                         (Python virtual environment)
├── src/user_main.c               (ESP8266 firmware)
├── include/user_config.h         (Configuration)
├── platformio.ini                (Build configuration)
├── nerf_gun_controller.py        (Python controller)
├── find_esp8266.py              (Network scanner)
├── useful.md                     (Command reference)
├── README.md                     (Project documentation)
└── requirements.txt              (Python dependencies)
```

## 🚀 **Updated Commands (Simplified!)**

All commands now work from the project root directory:

### **Build & Upload**
```bash
cd /home/shinken/Documents/PlatformIO/Projects/ESP_WIFI_NERF

# Build
.venv/bin/pio run

# Upload
.venv/bin/pio run --target upload --upload-port /dev/ttyUSB0

# Monitor
.venv/bin/pio device monitor --port /dev/ttyUSB0 --baud 115200
```

### **Python Scripts**
```bash
# Find ESP8266 on network
.venv/bin/python find_esp8266.py

# Fire the nerf gun
.venv/bin/python nerf_gun_controller.py 192.168.1.30 fire

# Interactive mode
.venv/bin/python nerf_gun_controller.py 192.168.1.30 interactive
```

**Happy Nerfing! 🎯🔥**
