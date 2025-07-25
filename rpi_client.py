#!/usr/bin/env python3
"""
Raspberry Pi Controller Client
Simple client to interact with the RPi controller endpoints
"""

import requests
import json
import base64
import argparse
from datetime import datetime

class RPiController:
    def __init__(self, host="10.52.118.202", port=5000):
        self.base_url = f"http://{host}:{port}"
    
    def get_status(self):
        """Get status information from the RPi controller"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def fire(self):
        """Fire GPIO pin for 65ms"""
        try:
            response = requests.get(f"{self.base_url}/fire")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def half_fire(self):
        """Fire GPIO pin for 32ms"""
        try:
            response = requests.get(f"{self.base_url}/half_fire")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def fire_custom(self, duration_ms):
        """Fire GPIO pin for custom duration"""
        try:
            response = requests.get(f"{self.base_url}/fire/{duration_ms}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def capture_image(self, save_to_file=None):
        """Capture image from camera"""
        try:
            response = requests.get(f"{self.base_url}/camera/capture")
            data = response.json()
            
            if data.get('success') and save_to_file:
                # Decode base64 image and save
                image_data = base64.b64decode(data['image_data'])
                with open(save_to_file, 'wb') as f:
                    f.write(image_data)
                data['saved_to'] = save_to_file
            
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def capture_and_save_on_pi(self):
        """Capture and save image on Raspberry Pi"""
        try:
            response = requests.get(f"{self.base_url}/camera/capture/save")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='RPi Controller Client')
    parser.add_argument('--host', default='10.52.118.202', help='RPi host address')
    parser.add_argument('--port', default=5000, type=int, help='RPi port')
    parser.add_argument('action', choices=['status', 'fire', 'half_fire', 'capture', 'capture_save'], 
                       help='Action to perform')
    parser.add_argument('--duration', type=int, help='Custom fire duration in ms')
    parser.add_argument('--save', help='Save captured image to file')
    
    args = parser.parse_args()
    
    controller = RPiController(args.host, args.port)
    
    if args.action == 'status':
        result = controller.get_status()
    elif args.action == 'fire':
        if args.duration:
            result = controller.fire_custom(args.duration)
        else:
            result = controller.fire()
    elif args.action == 'half_fire':
        result = controller.half_fire()
    elif args.action == 'capture':
        result = controller.capture_image(args.save)
    elif args.action == 'capture_save':
        result = controller.capture_and_save_on_pi()
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
