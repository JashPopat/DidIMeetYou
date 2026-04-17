import dbf_manager
import sys
import time
import threading
from config import *
import crypto_utils
import udp_handler
import dbf_manager
import tcp_client

current_ephid      = None
current_ephid_lock = threading.Lock()
pending_encids      = []
pending_encids_lock = threading.Lock()
own_ephid_hashes = set()

# Task 1-3: Generate EphID, split into shares, and broadcast via UDP

def task123_loop(t, k, n):

    global current_ephid
    while True:
        # Task 1: Generate 32-Byte EphID
        ephid = crypto_utils.generate_ephid()
        with current_ephid_lock:
            current_ephid = ephid
        print(f"\n[Task 1] Generated New 32-Byte EphID: {ephid.hex()[:10]}")

        # Task 2: Split into n shares
        shares, ephid_hash = crypto_utils.get_shares_for_broadcast(ephid, k, n)
        own_ephid_hashes.add(ephid_hash)
        print(f"[Task 2] Generated {n} shares (k={k}). Verification Hash: {ephid_hash}")

        # Task 3: Trigger the UDP broadcast of these shares 
        udp_handler.broadcast_shares(shares, ephid_hash)
        
        time.sleep(t)

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 Dimy.py [t] [k] [n] [p]")
        sys.exit(1)

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

    print("--------------------------------")
    print("------- DIMY Node Active -------")
    print("--------------------------------")
    print(f"Parameters: t={t}, k={k}, n={n}, p={p}%")
    udp_handler.start_listener(k, p, own_ephid_hashes)
    print("[Main] UDP listener started.")
    dbf_manager.initialise_dbf()
    print("[Main] DBF initialised.")
    dbf_manager.start_dbf_rotation(t)    # Task 7
    print("[Main] DBF rotation started.")
    threading.Thread(target=task_5_encounter_loop, daemon=True).start()
    print("[Main] Encounter loop started.")
    threading.Thread(target=task_10_qbf_sync_loop, args=(t,), daemon=True).start()
    print("[Main] Task 10 QBF sync loop started.")
    multithread = threading.Thread(target=task123_loop, args=(t, k, n), daemon=True)
    multithread.start()

    try:
        print("\n>>> ---------- NODE ONLINE ------------ <<<")
        print(">>>Type 'positive' to report infection. <<<\n")
        while True:
            user_input = input().strip().lower()
            if user_input == 'positive':
                # Task 9
                cbf_data = dbf_manager.build_cbf() 
                if cbf_data:
                    import tcp_client
                    print("[Task 9] Uploading CBF to server...")
                    response = tcp_client.upload_to_server(cbf_data, is_cbf=True)
                    print(f"[Task 9] Server response: {response}")
                    print("[Task 9] Node entering positive state. Stopping QBFs.")
                    break 
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nNode shutting down...")

def handle_positive_diagnosis():
    cbf_data = dbf_manager.build_cbf()
    if cbf_data:
        response = tcp_client.upload_to_server(cbf_data, is_cbf=True)
        print(f"[Task 9] Server Confirmation: {response}")

def task_5_encounter_loop():
    while True:
        their_ephid = udp_handler.pop_reconstructed_ephid()
        if their_ephid is not None:
            with current_ephid_lock:
                our_ephid = current_ephid
            if our_ephid is None:
                print("[Task 5] Skipping — no current EphID yet.")
            elif their_ephid == our_ephid:
                print("[Task 5] Skipping — reconstructed own EphID, ignoring.")
            else:
                encID = crypto_utils.compute_encid(our_ephid, their_ephid)
                dbf_manager.add_encid(encID)  # Task 6
        time.sleep(1)

def check_for_positive_status():
    while True:
        cmd = input("\nType 'positive' to report infection: ").strip().lower()
        if cmd == 'positive':
            print("[Task 9] User diagnosed positive. Generating CBF...")
            cbf_data = dbf_manager.build_cbf()
            if cbf_data:
                import tcp_client
                tcp_client.upload_to_server(cbf_data, is_cbf=True)
                print("[Task 9] Stopping generation of QBFs.")
                break

def task_10_qbf_sync_loop(t):
    dt_seconds = 30  # Dt calculation: every (t * 6 * 6) / 60 minutes - changed for TESTING only
    while True:
        time.sleep(dt_seconds)
        qbf_data = dbf_manager.build_qbf()
        
        if qbf_data:
            print("[Task 10] Sending QBF to backend...")
            # Task 10
            import tcp_client
            result = tcp_client.upload_to_server(qbf_data, is_cbf=False)
            print(f"[Task 10] Result from server: {result.upper()}")
            
            if result.lower() == "matched":
                print("[Task 10] Notification: You have been in close contact with a positive case!")

if __name__ == "__main__":
    main()