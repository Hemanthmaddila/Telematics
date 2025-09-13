import socket
import sys

# Database connection parameters
DB_HOST = "telematics-db.cteio0ogsw3d.us-east-2.rds.amazonaws.com"
DB_PORT = 5432

def test_network_connectivity():
    try:
        print(f"Testing network connectivity to {DB_HOST}:{DB_PORT}...")
        # Test if we can reach the host on the specified port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        result = sock.connect_ex((DB_HOST, DB_PORT))
        sock.close()
        
        if result == 0:
            print("✅ Network connectivity: SUCCESS")
            print("   The database host is reachable on port 5432")
        else:
            print("❌ Network connectivity: FAILED")
            print("   Cannot reach the database host on port 5432")
            print("   This could be due to:")
            print("   1. Security group not allowing inbound connections")
            print("   2. RDS instance not in a public subnet")
            print("   3. Network ACLs blocking traffic")
            print("   4. RDS instance not in 'Available' state")
            
    except Exception as e:
        print(f"❌ Network test failed: {e}")

if __name__ == "__main__":
    test_network_connectivity()