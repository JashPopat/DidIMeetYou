import socket
import time
import json
import threading
import random
from config import SHARE_BROADCAST_INTERVAL
from secret_sharing import reconstruct_id
from crypto_utils import get_ephid_hash

# new shared state variables
received_shares = {}
reconstructed_ephids = {}
shares_lock = threading.Lock()


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
                    "y": str(y)
                }
                message = json.dumps(packet).encode('utf-8')
                
                # Send the share
                sock.sendto(message, broadcast_addr)
                print(f"[Task 3] Broadcasted share {x} for EphID hash: {ephid_hash}")
               # Wait 3 seconds before sending the next unique share
                time.sleep(SHARE_BROADCAST_INTERVAL)

    # Start the broadcast loop in its own thread
    threading.Thread(target=run_broadcast, daemon=True).start()

def start_listener(k, p, own_hashes=None):
    """
    Task 3a: Listen for incoming UDP shares and apply drop mechanism.
    Task 4:  Once k shares collected, attempt reconstruction and verify.
 
    Parameters:
        k : minimum shares needed to reconstruct EphID
        p : drop probability as integer percent (e.g. 40 means 40%)
    """
    def run_listener():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # SO_REUSEADDR allows multiple nodes on same machine to share this port
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
                    # --------------------------------------------------
                    # Parse the incoming share packet
                    # --------------------------------------------------
                    try:
                        packet = json.loads(data.decode('utf-8'))
                        ephid_hash = packet['hash']
                        x = int(packet['x'])
                        y = int(packet['y'])    # was string in JSON, convert back
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"[Task 3a] Malformed packet from {addr}: {e}")
                        continue
                    if own_hashes is not None and ephid_hash in own_hashes:
                        continue    # ignore our own broadcasts

                    # --------------------------------------------------
                    # Task 3a: Drop mechanism
                    # Generate a random float between 0 and 1
                    # If it is less than p/100, drop the share entirely
                    # e.g. p=40 → drop if roll < 0.40
                    # --------------------------------------------------
                    drop_roll = random.random()
                    drop_threshold = p / 100.0
 
                    if drop_roll < drop_threshold:
                        print(f"[Task 3a] Share DROPPED "
                              f"(roll={drop_roll:.2f} < threshold={drop_threshold:.2f})")
                        continue    # skip this share, do not process it
 
                    print(f"[Task 3a] Received share (x={x}) "
                          f"for EphID hash: {ephid_hash[:8]}... "
                          f"from {addr[0]}")
 
                    # --------------------------------------------------
                    # Task 3a: Track received shares grouped by ephid_hash
                    # This sets up Task 4 — once we have k shares we can
                    # attempt reconstruction
                    # --------------------------------------------------
                    with shares_lock:
                        if ephid_hash in reconstructed_ephids:
                            continue
                        # Initialise list for this hash if first share seen
                        if ephid_hash not in received_shares:
                            received_shares[ephid_hash] = []
 
                        # Avoid storing duplicate shares (same x value)
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
# ============================================================
# TASK 4 — RECONSTRUCT + VERIFY
# Called internally once we have k shares for an EphID
# ============================================================
def _attempt_reconstruction(ephid_hash, shares):
    """
    Task 4: Reconstruct EphID from k shares and verify using hash.
 
    Called inside shares_lock so state is already thread safe.
    Uses Lagrange interpolation from secret_sharing.py to reconstruct,
    then verifies by hashing and comparing to the advertised hash.
 
    Parameters:
        ephid_hash : the hash sent alongside the shares (for verification)
        shares     : list of exactly k (x, y) tuples
    """
    print(f"\n[Task 4] Attempting reconstruction for {ephid_hash[:8]}...")
 
    try:
        # Reconstruct the EphID bytes using Lagrange interpolation
        reconstructed_ephid = reconstruct_id(shares)
 
        # --------------------------------------------------
        # Task 4: Verify by hashing the reconstructed EphID
        # Take first 16 chars to match what was sent in the broadcast packet
        # --------------------------------------------------
        computed_hash = get_ephid_hash(reconstructed_ephid)[:16]
 
        if computed_hash == ephid_hash:
            # Success
            print(f"[Task 4] EphID reconstruction DONE. "
                  f"EphID: {reconstructed_ephid.hex()[:6]}")
            print(f"[Task 4] Hash verified ✓  "
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
 
 
# ============================================================
# GETTER — used by Dimy.py for Task 5
# Returns a reconstructed EphID and removes it from the dict
# so each encounter is only processed once
# ============================================================
 
def pop_reconstructed_ephid():
    """
    Returns the next available reconstructed EphID (if any) and
    removes it from storage so it is only processed once.
    Called by Dimy.py to trigger Task 5.
 
    Returns:
        bytes if an EphID is available, None otherwise
    """
    with shares_lock:
        if reconstructed_ephids:
            hash_key = next(iter(reconstructed_ephids))
            return reconstructed_ephids.pop(hash_key)
        return None