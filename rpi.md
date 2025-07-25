# Raspberry Pi Controller Functions

## Server Endpoints (RPi: 10.52.118.202:5000)

### Status
- **GET /** - Get system status and available endpoints

### Camera Functions
- **GET /camera/capture** - Capture image and return as base64 JSON
- **GET /camera/capture/save** - Capture and save image on Pi (/home/pi/Pictures/)

### GPIO Functions (Pin 18)
- **GET /fire** - Fire GPIO for 65ms (HIGH → LOW)
- **GET /half_fire** - Fire GPIO for 32ms (half duration)
- **GET /fire/{duration}** - Fire GPIO for custom duration (1-5000ms)

## Client Usage Examples

```bash
# Check status
python3 rpi_client.py status

# Camera functions
python3 rpi_client.py capture --save image.jpg    # Download to laptop
python3 rpi_client.py capture_save                # Save on Pi

# GPIO functions
python3 rpi_client.py fire                        # 65ms trigger
python3 rpi_client.py half_fire                   # 32ms trigger
python3 rpi_client.py fire --duration 100         # Custom duration
```

## Direct HTTP Calls

```bash
# Status
curl http://10.52.118.202:5000/

# Fire functions
curl http://10.52.118.202:5000/fire
curl http://10.52.118.202:5000/half_fire
curl http://10.52.118.202:5000/fire/150

# Camera
curl http://10.52.118.202:5000/camera/capture
curl http://10.52.118.202:5000/camera/capture/save
```

## Service Management (on Pi)

```bash
# Check service status
sudo systemctl status rpi-controller.service

# Restart service
sudo systemctl restart rpi-controller.service

# View logs
sudo journalctl -u rpi-controller.service -f
```

## Auto-Start
✅ Service automatically starts on Pi boot
✅ Runs on port 5000
✅ Camera: IMX219 detected and working
✅ GPIO: Pin 18 configured for output
