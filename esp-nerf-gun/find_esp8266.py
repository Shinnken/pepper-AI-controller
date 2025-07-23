#!/usr/bin/env python3
"""
ESP WiFi Nerf Gun Finder
Scans local network to find the ESP8266 nerf gun controller
"""

import subprocess
import requests
import socket
import threading
from concurrent.futures import ThreadPoolExecutor

def get_local_network():
    """Get the local network range"""
    try:
        # Get default gateway
        result = subprocess.run(['ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse output to get network interface
            for line in result.stdout.split('\n'):
                if 'default' in line:
                    parts = line.split()
                    if 'dev' in parts:
                        dev_index = parts.index('dev')
                        if dev_index + 1 < len(parts):
                            interface = parts[dev_index + 1]
                            break
        
        # Get IP address of the interface
        result = subprocess.run(['ip', 'addr', 'show', interface], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'inet ' in line and not '127.0.0.1' in line:
                    ip_part = line.strip().split()[1]
                    network = ip_part.split('/')[0]
                    # Assume /24 network
                    base_ip = '.'.join(network.split('.')[:-1])
                    return base_ip
    except:
        pass
    
    # Fallback - try common networks
    return "192.168.1"

def check_esp8266(ip):
    """Check if IP address has the ESP8266 nerf gun"""
    try:
        response = requests.get(f"http://{ip}/status", timeout=2)
        if response.status_code == 200:
            try:
                data = response.json()
                if 'status' in data:
                    return ip, data
            except:
                # Check if it contains nerf gun HTML
                if 'nerf' in response.text.lower():
                    return ip, {"status": "found", "message": "HTML response"}
        return None
    except:
        return None

def scan_network():
    """Scan network for ESP8266 devices"""
    base_ip = get_local_network()
    print(f"🔍 Scanning network {base_ip}.x for ESP8266 Nerf Gun...")
    print("This may take a minute...")
    
    found_devices = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            futures.append(executor.submit(check_esp8266, ip))
        
        for i, future in enumerate(futures):
            result = future.result()
            if result:
                ip, data = result
                found_devices.append((ip, data))
                print(f"🎯 Found ESP8266 Nerf Gun at: {ip}")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', 'N/A')}")
            
            # Show progress
            if (i + 1) % 50 == 0:
                print(f"   Checked {i + 1}/254 addresses...")
    
    return found_devices

def test_nerf_gun(ip):
    """Test the nerf gun at the given IP"""
    print(f"\n🎮 Testing nerf gun at {ip}...")
    
    try:
        # Test status
        print("📡 Checking status...")
        response = requests.get(f"http://{ip}/status", timeout=5)
        if response.status_code == 200:
            print("✅ Status check successful!")
            try:
                data = response.json()
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', 'N/A')}")
            except:
                print(f"   Raw response: {response.text[:100]}...")
        
        # Test fire command
        input("\n🔥 Press Enter to test FIRE command (make sure nerf gun is safe)...")
        print("🎯 Sending fire command...")
        response = requests.get(f"http://{ip}/fire", timeout=5)
        if response.status_code == 200:
            print("🎉 Fire command sent successfully!")
            try:
                data = response.json()
                print(f"   Response: {data.get('message', 'N/A')}")
            except:
                print(f"   Raw response: {response.text[:100]}...")
            print("💡 Check if the LED on ESP8266 blinked rapidly!")
        else:
            print(f"❌ Fire command failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    print("🎯 ESP WiFi Nerf Gun Finder & Tester")
    print("=" * 40)
    
    # Scan for devices
    devices = scan_network()
    
    if not devices:
        print("\n❌ No ESP8266 Nerf Gun found on the network")
        print("\nTroubleshooting tips:")
        print("1. Make sure ESP8266 is powered on")
        print("2. Check that it connected to WiFi (LED should blink slowly)")
        print("3. Verify WiFi credentials in user_config.h are correct")
        print("4. Try manually specifying IP address")
        
        # Manual IP option
        manual_ip = input("\n🔧 Enter ESP8266 IP address manually (or press Enter to skip): ").strip()
        if manual_ip:
            test_nerf_gun(manual_ip)
        return
    
    print(f"\n🎉 Found {len(devices)} ESP8266 device(s)!")
    
    if len(devices) == 1:
        ip, data = devices[0]
        test_nerf_gun(ip)
    else:
        print("\nMultiple devices found:")
        for i, (ip, data) in enumerate(devices):
            print(f"{i+1}. {ip} - {data.get('message', 'N/A')}")
        
        choice = input(f"\nEnter choice (1-{len(devices)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(devices):
                ip, data = devices[idx]
                test_nerf_gun(ip)
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input")

if __name__ == "__main__":
    main()
