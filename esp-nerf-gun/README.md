# ESP WiFi Nerf Gun Controller

🎯 **WiFi-controlled Nerf Gun using ESP8266 with HTTP REST API, LED feedback, and Python controller scripts.**

## Features

- ✅ **WiFi HTTP REST API control**
- ✅ **Visual LED feedback** (rapid blink on fire)
- ✅ **Python controller** with multiple modes
- ✅ **Web browser interface**
- ✅ **Automatic network discovery**
- ✅ **Configurable trigger duration**
- ✅ **Rapid fire mode**
- ✅ **Interactive control mode**

## 🔧 Hardware Setup

### Components Needed:
- ESP8266 development board (NodeMCU, Wemos D1, etc.)
- Servo motor or solenoid to trigger the nerf gun
- Transistor (2N2222 or similar) or relay module
- Resistor (1kΩ)
- Breadboard and jumper wires
- Power supply (if needed for servo/solenoid)

### Wiring:
```
ESP8266 GPIO12 (D6) -> Base of transistor (through 1kΩ resistor)
Transistor Collector -> Servo/Solenoid positive
Transistor Emitter   -> Ground
Servo/Solenoid negative -> Ground
```

For a relay module:
```
ESP8266 GPIO12 (D6) -> Relay IN pin
ESP8266 3.3V        -> Relay VCC
ESP8266 GND         -> Relay GND
Relay NO/COM        -> Servo/Solenoid circuit
```

## 📝 Software Setup

### 1. Configure WiFi Credentials

Edit `include/user_config.h` and replace with your WiFi details:

```c
#define WIFI_SSID "Your_WiFi_Network_Name"
#define WIFI_PASSWORD "Your_WiFi_Password"
```

### 2. Build and Upload Firmware

```bash
# In the project directory
pio run
pio run --target upload
```

### 3. Find ESP8266 IP Address

Monitor the serial output to find the assigned IP address:

```bash
pio device monitor
```

Look for output like:
```
Connected to WiFi
Got IP: 192.168.1.100
HTTP server started on port 80
```

## 🎯 Usage

### Python Script

Install required dependencies:
```bash
pip install requests
```

Basic usage:
```bash
# Fire once
python3 nerf_gun_controller.py 192.168.1.100 fire

# Check status
python3 nerf_gun_controller.py 192.168.1.100 status

# Rapid fire (5 shots, 1 second delay)
python3 nerf_gun_controller.py 192.168.1.100 rapid 5 --delay 1.0

# Interactive mode
python3 nerf_gun_controller.py 192.168.1.100 interactive
```

### Web Interface

1. Open `web_controller.html` in your web browser
2. Enter the ESP8266's IP address
3. Click the "FIRE!" button to shoot
4. Use "Status" to check if the device is ready
5. Use "Rapid Fire" for multiple shots

### HTTP API

The ESP8266 exposes these endpoints:

- `GET /fire` - Fire the nerf gun
- `GET /status` - Check device status
- `GET /` - Basic info page

Example with curl:
```bash
curl http://192.168.1.100/fire
curl http://192.168.1.100/status
```

## ⚙️ Configuration

You can modify these settings in `include/user_config.h`:

```c
#define NERF_TRIGGER_PIN 12        // GPIO pin connected to trigger circuit
#define NERF_TRIGGER_DURATION 500  // How long to activate trigger (ms)
#define HTTP_SERVER_PORT 80        // Web server port
```

## 🔒 Safety Considerations

- **Always treat the nerf gun as if it's loaded**
- **Never point at people, faces, or fragile objects**
- **Use appropriate eye protection**
- **Ensure clear firing range before triggering**
- **Test the mechanical trigger system thoroughly**
- **Consider adding a safety switch or confirmation mechanism**
- **Secure your WiFi network to prevent unauthorized access**

## 🛠️ Troubleshooting

### ESP8266 won't connect to WiFi:
- Check WiFi credentials in `user_config.h`
- Ensure 2.4GHz WiFi (ESP8266 doesn't support 5GHz)
- Check signal strength

### Can't trigger the nerf gun:
- Verify wiring connections
- Check if GPIO12 voltage changes (use multimeter)
- Test servo/solenoid with direct power connection
- Adjust `NERF_TRIGGER_DURATION` if needed

### Connection timeouts:
- Verify ESP8266 IP address
- Check if both devices are on same network
- Try pinging the ESP8266: `ping 192.168.1.100`
- Check firewall settings

### Serial monitor shows errors:
- Verify all connections are secure
- Check power supply capacity
- Look for specific error messages in serial output

## 📡 Network Commands

Find ESP8266 on your network:
```bash
# Scan for devices (Linux/Mac)
nmap -sn 192.168.1.0/24

# Find by MAC address (Espressif devices)
arp -a | grep -i "espressif\|esp"
```

## 🔄 Advanced Features

### Custom Trigger Patterns
Modify the `fire_nerf_gun()` function to create custom firing patterns:

```c
void fire_nerf_gun(void)
{
    // Double tap pattern
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 1);
    os_delay_us(200000);  // 200ms
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 0);
    os_delay_us(100000);  // 100ms
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 1);
    os_delay_us(200000);  // 200ms
    GPIO_OUTPUT_SET(NERF_TRIGGER_PIN, 0);
}
```

### Add Authentication
For security, you can add simple authentication:

```c
// In http_recv_cb function
if (os_strstr(data, "Authorization: Bearer YOUR_SECRET_TOKEN") == NULL) {
    // Send 401 Unauthorized
    return;
}
```

## 📞 Support

If you encounter issues:
1. Check the serial monitor output for debug messages
2. Verify all hardware connections
3. Test components individually
4. Check network connectivity
5. Review the troubleshooting section

## ⚠️ Disclaimer

This project is for educational purposes. Users are responsible for safe operation and compliance with local laws and regulations regarding projectile devices.
