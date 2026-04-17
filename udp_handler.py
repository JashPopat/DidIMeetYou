import socket
import time
import json
import threading
import random
from config import SHARE_BROADCAST_INTERVAL
from secret_sharing import reconstruct_id
from crypto_utils import get_ephid_hash

received_shares = {}
reconstructed_ephids = {}
shares_lock = threading.Lock()

# Task 3

def broadcast_shares(shares, ephid_hash):
    def run_broadcast():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # 255.255.255.255 is local network, do not change thx
            broadcast_addr = ('255.255.255.255', 5000)
            for x, y in shares:
                packet = {
                    "hash": ephid_hash,
                    "x": x,
                    "y": str(y)
                }
                message = json.dumps(packet).encode('utf-8')
                sock.sendto(message, broadcast_addr)
                print(f"[Task 3] Broadcasted share {x} for EphID hash: {ephid_hash}")
                time.sleep(SHARE_BROADCAST_INTERVAL)

    threading.Thread(target=run_broadcast, daemon=True).start()

# Task 3a and 4
def start_listener(k, p, own_hashes=None):
    def run_listener():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Mac seems to have issues with the port reuse so I added this in - Jash
            if hasattr(socket, 'SO_REUSEPORT'):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(('', 5000))
            print(f"[Task 3a] Listening for UDP shares on port 5000 "
                  f"(drop probability: {p}%)")
            while True:
                try:
                    data, addr = sock.recvfrom(65535)
                    try:
                        packet = json.loads(data.decode('utf-8'))
                        ephid_hash = packet['hash']
                        x = int(packet['x'])
                        y = int(packet['y'])
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"[Task 3a] Malformed packet from {addr}: {e}")
                        continue
                    if own_hashes is not None and ephid_hash in own_hashes:
                        continue    # ignore our own broadcasts

                    drop_roll = random.random()
                    drop_threshold = p / 100.0
 
                    if drop_roll < drop_threshold:
                        print(f"[Task 3a] Share DROPPED "
                              f"(roll={drop_roll:.2f} < threshold={drop_threshold:.2f})")
                        continue    # skip this share
 
                    print(f"[Task 3a] Received share (x={x}) "
                          f"for EphID hash: {ephid_hash[:8]}... "
                          f"from {addr[0]}")
 
                    with shares_lock:
                        if ephid_hash in reconstructed_ephids:
                            continue
                        # Initialise list for this hash if first share seen
                        if ephid_hash not in received_shares:
                            received_shares[ephid_hash] = []
 
                        existing_x_values = [s[0] for s in received_shares[ephid_hash]]
                        if x in existing_x_values:
                            print(f"[Task 3a] Duplicate share (x={x}) ignored.")
                            continue
 
                        # Store the share
                        received_shares[ephid_hash].append((x, y))
                        share_count = len(received_shares[ephid_hash])
                        
 
                        print(f"[Task 3a] Stored share for {ephid_hash[:8]}... "
                              f"— {share_count}/{k} shares collected so far")
                        

                        if share_count >= k:
                            _attempt_reconstruction(ephid_hash, received_shares[ephid_hash][:k])

                except Exception as e:
                    print(f"[Task 3a] Unexpected error: {e}")
    threading.Thread(target=run_listener, daemon=True).start()
def _attempt_reconstruction(ephid_hash, shares):

    print(f"\n[Task 4] Attempting reconstruction for {ephid_hash[:8]}...")
 
    try:
        reconstructed_ephid = reconstruct_id(shares)
 
        computed_hash = get_ephid_hash(reconstructed_ephid)[:16]
 
        if computed_hash == ephid_hash:
            # Success
            print(f"[Task 4] EphID reconstruction DONE. "
                  f"EphID: {reconstructed_ephid.hex()[:6]}")
            print(f"[Task 4] Hash verified — reconstruction SUCCESSFUL. "
                  f"expected={ephid_hash[:8]}  computed={computed_hash[:8]}")
 
            # Store reconstructed EphID
            reconstructed_ephids[ephid_hash] = reconstructed_ephid
 
            # Clean up shares — no longer needed
            if ephid_hash in received_shares:
                del received_shares[ephid_hash]
 
        else:
            # Hash mismatch — reconstruction failed
            print("[Task 4] Reconstruction FAILED — hash mismatch.")
            print(f"[Task 4]   Expected : {ephid_hash}")
            print(f"[Task 4]   Computed : {computed_hash}")
 
    except Exception as e:
        print(f"[Task 4] Reconstruction error: {e}")
 
def pop_reconstructed_ephid():
    with shares_lock:
        if reconstructed_ephids:
            hash_key = next(iter(reconstructed_ephids))
            return reconstructed_ephids.pop(hash_key)
        return None