import socket
import json
import base64
from config import SERVER_PORT

def run_server():
    stored_cbfs = []
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow restart
        s.bind(('0.0.0.0', SERVER_PORT))
        s.listen()
        print(f"DimyServer listening on port {SERVER_PORT}...")
        
        while True:
            conn, addr = s.accept()
            with conn:
                full_data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    full_data += chunk
                    # Check if we have the full JSON (ends with })
                    if full_data.endswith(b"}"):
                        break
                
                if not full_data: continue
                
                try:
                    payload = json.loads(full_data.decode('utf-8'))
                    if payload['type'] == 'CBF':
                        cbf_bytes = base64.b64decode(payload['data'])
                        stored_cbfs.append(cbf_bytes)
                        print(f"\n[Task 9] Successfully stored CBF from {addr}")
                        conn.sendall(b"CBF Upload Successful")

                    if payload['type'] == 'QBF':
                        qbf_bytes = base64.b64decode(payload['data'])
                        match_found = False
                        
                        # Task 10: Perform overlap matching
                        for stored_cbf in stored_cbfs:
                            overlap_bits = 0
                            
                            # Perform bitwise AND to find the intersection
                            for i in range(len(qbf_bytes)):
                                # Count the '1's in the intersection of this byte
                                overlap_bits += bin(qbf_bytes[i] & stored_cbf[i]).count('1')
                                
                                # Early exit: If we've found at least 3 overlapping bits, it's a match!
                                if overlap_bits >= 3: 
                                    break
                            
                            if overlap_bits >= 3:
                                match_found = True
                                break
                                
                        if match_found:
                            print(f"[Task 10] Match found for {addr}!")
                            conn.sendall(b"matched")
                        else:
                            print(f"[Task 10] No match for {addr}.")
                            conn.sendall(b"not matched")
                            
                except json.JSONDecodeError as e:
                    print(f"[Error] Failed to decode JSON: {e}")

if __name__ == "__main__":
    run_server()