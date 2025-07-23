# ESP WiFi Nerf Gun Controller - Command Reference

## 🎯 Project Overview
WiFi-controlled nerf gun using ESP8266 with HTTP REST API, LED feedback, and Python controller scripts.

---

## 🔧 Development Commands

### **Build Project**
```bash
# Build firmware for all configured boards
.venv/bin/pio run

# Build for specific board only
.venv/bin/pio run -e nodemcuv2
.venv/bin/pio run -e esp12e
```

### **Upload Firmware**
```bash
# Upload to ESP8266 (auto-detect port)
.venv/bin/pio run --target upload

# Upload to specific port
.venv/bin/pio run --target upload --upload-port /dev/ttyUSB0

# Upload specific environment
.venv/bin/pio run -e nodemcuv2 --target upload --upload-port /dev/ttyUSB0
```

### **Serial Monitor**
```bash
# Monitor serial output
.venv/bin/pio device monitor --port /dev/ttyUSB0 --baud 115200

# Monitor with automatic port detection
.venv/bin/pio device monitor

# Exit monitor: Ctrl+C
```

### **Clean Build**
```bash
# Clean build files
.venv/bin/pio run --target clean
```

---

## 🌐 Network & Discovery Commands

### **Find ESP8266 on Network**
```bash
# Automatic network scan and test
.venv/bin/python find_esp8266.py

# Check specific IP manually
curl http://192.168.1.30/status
```

### **Check USB Devices**
```bash
# List USB devices (find ESP8266)
lsusb

# List serial ports
ls -la /dev/ttyUSB*
ls -la /dev/ttyACM*

# Check user permissions
groups $USER
```

---

## 🎮 Python Controller Commands

### **Single Fire**
```bash
# Fire once
.venv/bin/python nerf_gun_controller.py 192.168.1.30 fire

# Replace 192.168.1.30 with your ESP8266's IP address
```

### **Status Check**
```bash
# Check if nerf gun is ready
.venv/bin/python nerf_gun_controller.py 192.168.1.30 status
```

### **Rapid Fire**
```bash
# Rapid fire: 3 shots with 1 second delay
.venv/bin/python nerf_gun_controller.py 192.168.1.30 rapid 3 1

# Rapid fire: 5 shots with 0.5 second delay
.venv/bin/python nerf_gun_controller.py 192.168.1.30 rapid 5 0.5
```

### **Interactive Mode**
```bash
# Start interactive controller
.venv/bin/python nerf_gun_controller.py 192.168.1.30 interactive

# Available commands in interactive mode:
# - fire          : Fire once
# - status         : Check status
# - rapid 3 1      : Rapid fire 3 shots with 1s delay
# - quit / exit / q: Exit interactive mode
```

---

## 🌐 HTTP API Commands

### **Using curl**
```bash
# Fire the nerf gun
curl http://192.168.1.30/fire

# Check status
curl http://192.168.1.30/status

# Get web interface
curl http://192.168.1.30/
```

### **Web Browser**
```
# Open in browser for web interface:
http://192.168.1.30

# Direct API endpoints:
http://192.168.1.30/fire    - Fire the nerf gun
http://192.168.1.30/status  - Check status
```

---

## ⚙️ Configuration

### **WiFi Settings** (user_config.h)
```c
#define WIFI_SSID "Your_WiFi_Name"
#define WIFI_PASSWORD "Your_WiFi_Password"
```

### **Hardware Settings** (user_config.h)
```c
#define NERF_TRIGGER_PIN 12           // GPIO12 - D6 on NodeMCU
#define STATUS_LED_PIN 2              // GPIO2 - Built-in LED
#define NERF_TRIGGER_DURATION 65      // milliseconds
#define HTTP_SERVER_PORT 80           // Web server port
```

---

## 🔧 Hardware Setup

### **Connections**
- **GPIO12 (D6 on NodeMCU)**: Connect nerf gun trigger mechanism
- **GPIO2**: Built-in LED (automatic - no connection needed)
- **VIN/3.3V**: Power for external components if needed
- **GND**: Ground connection

### **NodeMCU Pin Mapping**
```
GPIO12 = D6    (Nerf Trigger)
GPIO2  = D4    (Built-in LED)
```

---

## 🚨 Troubleshooting

### **Upload Issues**
```bash
# Check if ESP8266 is detected
lsusb | grep -i "ch340\|cp210\|ftdi"

# Check port permissions
ls -la /dev/ttyUSB0

# Add user to dialout group (if needed)
sudo usermod -a -G dialout $USER
# Logout and login again after this command
```

### **Network Issues**
```bash
# Scan for ESP8266 on network
.venv/bin/python find_esp8266.py

# Check WiFi credentials in user_config.h
# Monitor serial output during boot to see connection status
.venv/bin/pio device monitor --port /dev/ttyUSB0 --baud 115200
```

### **Build Issues**
```bash
# Clean and rebuild
.venv/bin/pio run --target clean
.venv/bin/pio run
```

---

## 📱 Quick Start Sequence

1. **Configure WiFi** in `include/user_config.h`
2. **Build**: `.venv/bin/pio run`
3. **Upload**: `.venv/bin/pio run --target upload --upload-port /dev/ttyUSB0`
4. **Find ESP**: `.venv/bin/python find_esp8266.py`
5. **Test Fire**: `.venv/bin/python nerf_gun_controller.py <IP> fire`

---

## 📝 Project Files

- **`src/user_main.c`**: Main ESP8266 firmware code
- **`include/user_config.h`**: Configuration settings
- **`nerf_gun_controller.py`**: Python controller script
- **`find_esp8266.py`**: Network scanner and tester
- **`platformio.ini`**: Build configuration
- **`useful.md`**: This command reference file

---

## 🎯 Features

- ✅ WiFi HTTP REST API control
- ✅ Visual LED feedback (rapid blink on fire)
- ✅ Python controller with multiple modes
- ✅ Web browser interface
- ✅ Automatic network discovery
- ✅ Configurable trigger duration
- ✅ Rapid fire mode
- ✅ Interactive control mode

**Happy Nerfing! 🎯🔥**
