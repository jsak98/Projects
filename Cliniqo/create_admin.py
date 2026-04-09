"""
Run this ONCE after setting up the database to create the first doctor account.
Usage: python create_admin.py
"""
import bcrypt
from db.connection import DBConn

name     = input("Doctor's full name: ").strip()
email    = input("Email: ").strip()
password = input("Password: ").strip()

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

with DBConn() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, 'doctor')
            ON CONFLICT (email) DO UPDATE SET password = EXCLUDED.password
        """, (name, email, hashed))

print(f"\n✅ Doctor account created for {name} ({email})")
print("You can now log in via the Streamlit app.")
