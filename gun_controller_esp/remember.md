# Fire once
/home/shinken/Documents/PlatformIO/Projects/ESP_test/.venv/bin/python nerf_gun_controller.py 192.168.1.30 fire

# Check status
/home/shinken/Documents/PlatformIO/Projects/ESP_test/.venv/bin/python nerf_gun_controller.py 192.168.1.30 status

# Rapid fire (3 shots with 1 second delay)
/home/shinken/Documents/PlatformIO/Projects/ESP_test/.venv/bin/python nerf_gun_controller.py 192.168.1.30 rapid 3 1

# Interactive mode
/home/shinken/Documents/PlatformIO/Projects/ESP_test/.venv/bin/python nerf_gun_controller.py 192.168.1.30 interactive

# Fire the nerf gun
curl http://192.168.1.30/fire

# Check status
curl http://192.168.1.30/status

# Or open in browser: http://192.168.1.30


🔧 Hardware Setup:
GPIO12 (D6): Connect your nerf gun trigger mechanism here
GPIO2: LED blinks rapidly when firing (already working!)
Trigger Duration: 500ms (configurable in user_config.h)
🎮 Your System Features:
✅ WiFi controlled
✅ HTTP REST API
✅ Visual LED feedback
✅ Python controller script
✅ Interactive mode
✅ Rapid fire mode
✅ Web interface
Your ESP8266 WiFi Nerf Gun Controller is ready to go! Connect your trigger mechanism to GPIO12 and start having fun! 🎯🔥