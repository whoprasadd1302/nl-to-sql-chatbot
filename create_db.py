import sqlite3

conn = sqlite3.connect("chatbot.db")

cursor = conn.cursor()

# Chats table
cursor.execute("""
CREATE TABLE IF NOT EXISTS chats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT
)
""")

# Messages table
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    role TEXT,
    content TEXT,
    FOREIGN KEY(chat_id) REFERENCES chats(id)
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")