#!/usr/bin/env python3
"""
ESP WiFi Nerf Gun Controller - Python Script
Controls an ESP8266-powered nerf gun over WiFi
"""

import requests
import time
import sys
import argparse
from typing import Optional

class NerfGunController:
    def __init__(self, esp_ip: str, port: int = 80):
        self.base_url = f"http://{esp_ip}:{port}"
        self.timeout = 5  # seconds
    
    def fire(self) -> bool:
        """Fire the nerf gun"""
        try:
            print("🎯 Firing nerf gun...")
            response = requests.get(f"{self.base_url}/fire", timeout=self.timeout)
            
            if response.status_code == 200:
                print("✅ Success! Nerf gun fired!")
                try:
                    data = response.json()
                    print(f"📝 Response: {data.get('message', 'No message')}")
                except:
                    print(f"📝 Response: {response.text[:100]}...")
                return True
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout: ESP8266 did not respond")
            return False
        except requests.exceptions.ConnectionError:
            print("🔌 Connection Error: Could not connect to ESP8266")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def check_status(self) -> Optional[dict]:
        """Check if the nerf gun is ready"""
        try:
            print("📡 Checking nerf gun status...")
            response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Status: {data.get('status', 'unknown')}")
                    print(f"📝 Message: {data.get('message', 'No message')}")
                    return data
                except:
                    print(f"📝 Raw response: {response.text}")
                    return {"status": "connected", "message": response.text}
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout: ESP8266 did not respond")
            return None
        except requests.exceptions.ConnectionError:
            print("🔌 Connection Error: Could not connect to ESP8266")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def rapid_fire(self, shots: int, delay: float = 1.0):
        """Fire multiple shots with delay between them"""
        print(f"🎯 Starting rapid fire: {shots} shots with {delay}s delay")
        
        successful_shots = 0
        for i in range(shots):
            print(f"\n--- Shot {i+1}/{shots} ---")
            if self.fire():
                successful_shots += 1
            
            if i < shots - 1:  # Don't delay after the last shot
                print(f"⏸️  Waiting {delay} seconds...")
                time.sleep(delay)
        
        print(f"\n🏆 Rapid fire complete: {successful_shots}/{shots} successful shots")

def main():
    parser = argparse.ArgumentParser(description="ESP WiFi Nerf Gun Controller")
    parser.add_argument("esp_ip", help="IP address of the ESP8266")
    parser.add_argument("--port", "-p", type=int, default=80, help="Port (default: 80)")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Fire command
    fire_parser = subparsers.add_parser("fire", help="Fire the nerf gun once")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check nerf gun status")
    
    # Rapid fire command
    rapid_parser = subparsers.add_parser("rapid", help="Rapid fire multiple shots")
    rapid_parser.add_argument("shots", type=int, help="Number of shots")
    rapid_parser.add_argument("--delay", "-d", type=float, default=1.0, help="Delay between shots (seconds)")
    
    # Interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create controller
    controller = NerfGunController(args.esp_ip, args.port)
    
    if args.command == "fire":
        controller.fire()
        
    elif args.command == "status":
        controller.check_status()
        
    elif args.command == "rapid":
        controller.rapid_fire(args.shots, args.delay)
        
    elif args.command == "interactive":
        print("🎮 Interactive ESP WiFi Nerf Gun Controller")
        print("Commands: fire, status, rapid [shots] [delay], quit")
        
        while True:
            try:
                cmd = input("\n> ").strip().split()
                if not cmd:
                    continue
                    
                if cmd[0].lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                elif cmd[0].lower() == 'fire':
                    controller.fire()
                    
                elif cmd[0].lower() == 'status':
                    controller.check_status()
                    
                elif cmd[0].lower() == 'rapid':
                    shots = int(cmd[1]) if len(cmd) > 1 else 3
                    delay = float(cmd[2]) if len(cmd) > 2 else 1.0
                    controller.rapid_fire(shots, delay)
                    
                else:
                    print("❓ Unknown command. Use: fire, status, rapid [shots] [delay], quit")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except (ValueError, IndexError):
                print("❌ Invalid command format")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
