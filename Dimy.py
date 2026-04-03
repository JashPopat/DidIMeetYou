import sys
import time
import threading
from config import *
import crypto_utils
import udp_handler

def task_1_heartbeat(t, k, n):
    """
    This loop runs in the background, generating a new EphID 
    every 't' seconds and passing it to the secret sharing logic.
    """
    while True:
        # Task 1: Generate 32-Byte EphID
        ephid = crypto_utils.generate_ephid()
        print(f"\n[Task 1] Generated New 32-Byte EphID: {ephid.hex()[:10]}...")

        # Task 2: Split into n shares (Logic to be written in crypto_utils)
        shares, ephid_hash = crypto_utils.get_shares_for_broadcast(ephid, k, n)
        print(f"[Task 2] Generated {n} shares (k={k}). Verification Hash: {ephid_hash}")

        # Task 3: Trigger the UDP broadcast of these shares 
        udp_handler.broadcast_shares(shares, ephid_hash)
        
        time.sleep(t)

def main():
    # Validating command line arguments: python3 Dimy.py [t] [k] [n] [p] [Server_IP] [Server_Port]
    if len(sys.argv) < 5:
        print("Usage: python3 Dimy.py [t] [k] [n] [p]")
        sys.exit(1)

    # Parsing arguments
    try:
        t = int(sys.argv[1])
        k = int(sys.argv[2])
        n = int(sys.argv[3])
        p = int(sys.argv[4])
        if t not in [15,18,21,24,27,30]:
            print("t must be one of the following: 15, 18, 21, 24, 27, 30.")
            sys.exit(1)
        elif k < 3 or k > n:
            print("k must be at least 3 and less than or equal to n.")
            sys.exit(1)
        elif n < 5:
            print("n must be at least 5.")
            sys.exit(1)
    except ValueError:
        print("Error: t, k, n, and p must be integers.")
        sys.exit(1)

    print(f"--- DIMY Node Started ---")
    print(f"Parameters: t={t}, k={k}, n={n}, p={p}%")

    # Start the Task 1 Heartbeat in a background thread
    # This allows the main thread to handle UDP listening later (Task 3/4)
    multithread = threading.Thread(target=task_1_heartbeat, args=(t, k, n), daemon=True)
    multithread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nNode shutting down...")

if __name__ == "__main__":
    main()