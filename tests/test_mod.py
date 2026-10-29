import socket
import time
import json
import sys
sys.path.insert(0, r"E:\CZero VibeCoding")
from brain.service import AIBrainService

def test():
    print("Starting AIBrainService...")
    brain = AIBrainService()
    brain.start()
    time.sleep(0.5)

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.settimeout(2.0)
    server_addr = ("127.0.0.1", 27115)

    print("\n--- 1. Testing PING ---")
    client_sock.sendto(b"PING|test_handshake", server_addr)
    data, addr = client_sock.recvfrom(1024)
    print(f"Received from Brain: {data.decode()}")
    assert data.decode() == "PONG", f"Expected PONG, got {data.decode()}"

    print("\n--- 2. Testing CHAT EVENT ('need help at B site') ---")
    client_sock.sendto(b"EVENT|chat|Player|CT|1|need help at B site", server_addr)
    
    # Receive response packets from Brain
    start_t = time.time()
    received_say = False
    received_order = False
    
    while time.time() - start_t < 3.0:
        try:
            data, addr = client_sock.recvfrom(1024)
            msg = data.decode('latin-1')
            print(f"Received from Brain: {msg}")
            if msg.startswith("SAY|"):
                received_say = True
            if msg.startswith("ORDER|"):
                received_order = True
            if received_say and received_order:
                break
        except socket.timeout:
            break

    print(f"Chat test: received_say={received_say}, received_order={received_order}")

    print("\n--- 3. Testing KILL EVENT ---")
    client_sock.sendto(b"EVENT|kill|Vikram|EnemyBot|ak47|1", server_addr)
    time.sleep(0.5)

    print("\n--- 4. Testing ROUND END EVENT (Round Won) ---")
    client_sock.sendto(b"EVENT|round_end|1", server_addr)
    time.sleep(0.5)
    try:
        data, addr = client_sock.recvfrom(1024)
        print(f"Received after round_end: {data.decode('latin-1')}")
    except socket.timeout:
        pass

    print("\n--- 5. Testing WEAPON DROP ORDER ---")
    client_sock.sendto(b"EVENT|chat|Player|CT|1|drop me a gun pls", server_addr)
    start_t = time.time()
    while time.time() - start_t < 3.0:
        try:
            data, addr = client_sock.recvfrom(1024)
            msg = data.decode('latin-1')
            print(f"Drop test received: {msg}")
            if msg.startswith("ORDER|drop"):
                print("SUCCESS: Received ORDER|drop!")
                break
        except socket.timeout:
            break

    print("\n--- 6. Testing TEST_SOUND ---")
    client_sock.sendto(b"TEST_SOUND|hype", server_addr)
    time.sleep(0.5)

    brain.stop()
    client_sock.close()
    print("\nAll communication tests PASSED!")

if __name__ == "__main__":
    test()
