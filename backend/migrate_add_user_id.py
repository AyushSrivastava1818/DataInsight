import sqlite3

conn = sqlite3.connect('datainsight.db')
cursor = conn.cursor()

# Add user_id column to datasets table (nullable for backward compat with existing rows)
try:
    cursor.execute("ALTER TABLE datasets ADD COLUMN user_id VARCHAR")
    conn.commit()
    print("SUCCESS: user_id column added to datasets table.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("INFO: user_id column already exists, skipping.")
    else:
        raise
finally:
    conn.close()

print("SQLite schema migration complete.")
