import sqlite3
import os

# Try to find the database
db_paths = [
    'instance/eduquest.db',
    'eduquest.db', 
    'app.db',
    'database.db'
]

for path in db_paths:
    if os.path.exists(path):
        print(f"✅ Found database: {path}")
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Check feedback table structure
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        print("Feedback table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check if any feedback has admin_reply
        cursor.execute("SELECT id, name, message, admin_reply FROM feedback LIMIT 5")
        feedbacks = cursor.fetchall()
        print("\nSample feedback:")
        for f in feedbacks:
            print(f"  ID {f[0]}: {f[1]} - '{f[2][:50]}...' - Admin Reply: {f[3]}")
        
        conn.close()
        break
else:
    print("❌ No database file found!")