import time

def connect_bluetooth(retries=3, mac_address='00:21:13:02:1C:30', port=None):
    import socket
    """Connect to the Bluetooth device for shooting"""

    # If no port specified, use default RFCOMM port
    if port is None:
        port = 1  # Default RFCOMM port

    for attempt in range(retries):
        try:
            # Create Bluetooth socket using socket module
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.connect((mac_address, port))
            print(f"Connected to the Bluetooth device on port {port}")
            sock.settimeout(1)
            return sock
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(3)  # Wait before retrying
            else:
                print("Strzelamy na sucho")
                return None


bt = connect_bluetooth()
if bt is not None:
    bt.send(b'F\n')
    time.sleep(1)
    bt.close()