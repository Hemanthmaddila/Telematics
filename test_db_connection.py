import psycopg2
import sys

# Database connection parameters
DB_HOST = "telematics-db.cteio0ogsw3d.us-east-2.rds.amazonaws.com"
DB_PORT = "5432"
DB_NAME = "telematics"
DB_USER = "telematics_admin"
DB_PASSWORD = "Hemanth13"

def test_connection():
    try:
        print("Connecting to database...")
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        print("✅ Connected successfully!")
        cursor = conn.cursor()
        
        # Run a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        print("✅ Database connection test completed.")
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()