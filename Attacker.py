import socket
import json
import udp_handler
from crypto_utils import get_ephid_hash

def run_attacker():
    print("--- DIMY Attacker Node Active ---")
    print("[Attack] Listening for all UDP broadcasts on port 5000...")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        sock.bind(('', 5000))

        while True:
            data, addr = sock.recvfrom(65535)
            try:
                packet = json.loads(data.decode('utf-8'))
                ephid_hash = packet['hash']
                x = packet['x']
                y = packet['y']

                print(f"\n[Eavesdropped] From: {addr[0]}")
                print(f"    Hash : {ephid_hash}")
                print(f"    Share: (x={x}, y={y[:10]}...)")
                
            except Exception as e:
                continue

if __name__ == "__main__":
    run_attacker()
