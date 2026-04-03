import socket
import time
import json
import threading
from config import SHARE_BROADCAST_INTERVAL

def broadcast_shares(shares, ephid_hash):
    """
    Task 3: Broadcast n shares @ 1 unique share per 3 seconds.
    This runs in a separate thread so it doesn't block ID generation.
    """
    def run_broadcast():
        # Create a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Enable broadcasting mode
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Broadcast address and a port for all nodes to listen on
            # 255.255.255.255 sends to everyone on the local network
            broadcast_addr = ('255.255.255.255', 5000)

            for x, y in shares:
                # Prepare the packet
                packet = {
                    "hash": ephid_hash,
                    "x": x,
                    "y": y
                }
                message = json.dumps(packet).encode('utf-8')
                
                # Send the share
                sock.sendto(message, broadcast_addr)
                print(f"[Task 3] Broadcasted share {x} for EphID hash: {ephid_hash}")
                
                # Wait 3 seconds before sending the next unique share
                time.sleep(SHARE_BROADCAST_INTERVAL)

    # Start the broadcast loop in its own thread
    threading.Thread(target=run_broadcast, daemon=True).start()