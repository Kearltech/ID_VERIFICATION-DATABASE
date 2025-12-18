"""
Quick start script to setup database for ID Verification System
"""
print("="*60)
print("ID Verification System - Database Setup")
print("="*60)
print()

# Check if MySQL is running
print("Step 1: Checking MySQL connection...")
print("Please ensure MySQL Workbench shows a connection to:")
print("  Host: 127.0.0.1")
print("  Port: 3306")
print("  User: root")
print()

# Prompt for database setup
response = input("Have you created the 'IDverification' database? (y/n): ")

if response.lower() != 'y':
    print()
    print("Please create the database first:")
    print("1. Open MySQL Workbench")
    print("2. Connect to your MySQL instance")
    print("3. Run this SQL command:")
    print()
    print("   CREATE DATABASE IDverification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print()
    print("Then run this script again.")
    exit()

print()
print("Step 2: Setting up database tables...")
print()

# Get connection details
import getpass

host = input("MySQL Host [127.0.0.1]: ") or "127.0.0.1"
port = input("MySQL Port [3306]: ") or "3306"
user = input("MySQL Username [root]: ") or "root"
password = getpass.getpass("MySQL Password: ")
database = input("Database Name [IDverification]: ") or "IDverification"

print()
print("Connecting to database...")

try:
    # Import database setup
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from database.connection import initialize_database
    
    # Initialize connection
    db = initialize_database(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    
    # Test connection
    if not db.test_connection():
        print("❌ Failed to connect to database!")
        print("Please check your connection details and try again.")
        exit(1)
    
    print("✅ Connected to database successfully!")
    print()
    
    # Create tables
    print("Creating database tables...")
    db.create_tables()
    
    print()
    print("="*60)
    print("✅ Database Setup Complete!")
    print("="*60)
    print()
    print("Tables created:")
    print("  - users")
    print("  - submissions")
    print("  - validation_logs")
    print("  - api_usage")
    print("  - audit_logs")
    print()
    print("Next steps:")
    print("1. Run the Streamlit app: streamlit run app_gemini.py")
    print("2. In the sidebar, expand 'Database Settings'")
    print("3. Enter your MySQL credentials and click 'Connect'")
    print()
    print("For more information, see DATABASE_README.md")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Troubleshooting:")
    print("  - Ensure MySQL is running")
    print("  - Check your username and password")
    print("  - Verify the database exists")
    print("  - Check firewall settings")
    exit(1)
