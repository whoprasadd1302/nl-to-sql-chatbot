import sqlite3

conn = sqlite3.connect("chatbot.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM messages")
cursor.execute("DELETE FROM chats")

conn.commit()
conn.close()

print("All chat history deleted!")