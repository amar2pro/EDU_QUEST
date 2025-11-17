import sqlite3

# Connect to your database
conn = sqlite3.connect('eduquest.db')
cursor = conn.cursor()

print("Adding admin_reply column to feedback table...")

# Add the admin_reply column
cursor.execute("ALTER TABLE feedback ADD COLUMN admin_reply TEXT")
print("✅ Added admin_reply column")

# Add reply_date column (optional but useful)
cursor.execute("ALTER TABLE feedback ADD COLUMN reply_date DATETIME") 
print("✅ Added reply_date column")

conn.commit()
conn.close()
print("🎉 Database updated successfully!")