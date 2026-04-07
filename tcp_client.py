import socket
import json
import base64
from config import SERVER_PORT

def upload_to_server(bloom_filter_bytes, is_cbf=True):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', SERVER_PORT))
            
            payload = {
                "type": "CBF" if is_cbf else "QBF",
                "data": base64.b64encode(bloom_filter_bytes).decode('utf-8')
            }
            
            # Send everything
            s.sendall(json.dumps(payload).encode('utf-8'))
            
            # Signal we are done sending so server's recv loop can finish
            s.shutdown(socket.SHUT_WR) 
            
            response = s.recv(1024).decode('utf-8')
            return response
    except Exception as e:
        print(f"[TCP Error] {e}")
        return None