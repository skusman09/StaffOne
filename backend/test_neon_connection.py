"""Test Neon database connection."""
from app.database import engine

try:
    conn = engine.connect()
    print("Successfully connected to Neon PostgreSQL!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

