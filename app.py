
from flask import Flask, render_template, request, jsonify
from ollama import chat
import sqlite3

app = Flask(__name__)

# ==========================
# DATABASE FUNCTIONS
# ==========================

def create_chat(title="New Chat"):

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chats(title) VALUES(?)",
        (title,)
    )

    conn.commit()

    chat_id = cursor.lastrowid

    conn.close()

    return chat_id


def save_message(chat_id, role, content):

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (chat_id, role, content)
        VALUES (?, ?, ?)
        """,
        (chat_id, role, content)
    )

    conn.commit()
    conn.close()


def update_chat_title(chat_id, title):

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE chats
        SET title = ?
        WHERE id = ?
        """,
        (title, chat_id)
    )

    conn.commit()
    conn.close()

def get_chat_history(chat_id):

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE chat_id=?
        ORDER BY id
        """,
        (chat_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    history = []

    for role, content in rows:

        history.append(
            {
                "role": role,
                "content": content
            }
        )

    return history


# ==========================
# CURRENT CHAT
# ==========================

current_chat_id = None

# ==========================
# HOME
# ==========================

@app.route("/")
def home():

    return render_template("index.html")

# ==========================
# CHAT
# ==========================

@app.route("/chat", methods=["POST"])
def chatbot():

    global current_chat_id

    try:

        user_message = request.json["message"]
        history = get_chat_history(current_chat_id)

        if len(history) == 0:

            title = user_message[:30]

            update_chat_title(
                current_chat_id,
                title
            )

        print("\nUSER:", user_message)

        # Save user message
        save_message(
            current_chat_id,
            "user",
            user_message
        )

        # Load previous chat history
        history = get_chat_history(
            current_chat_id
        )

        # Keep only latest messages
        history = history[-20:]

        response = chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an expert AI assistant.

                    Your primary goal is to provide accurate, relevant, and complete answers.

                    Instructions:

                    - Answer only the user's question.
                    - Use conversation history when relevant.
                    - Do not introduce unrelated topics.
                    - Do not invent facts.
                    - If uncertain, explicitly say what is uncertain.
                    - Prefer correctness over creativity.
                    - Think carefully before answering.
                    - Break complex problems into steps.
                    - For technical questions:
                    * Explain concepts clearly.
                    * Provide examples.
                    * Use best practices.
                    - For coding questions:
                    * Provide working code.
                    * Explain key parts.
                    * Mention limitations when relevant.
                    - For database questions:
                    * Generate syntactically correct SQL.
                    * Consider schema information.
                    - Keep simple answers concise.
                    - Give detailed explanations when requested.
                    - Respond in the same language as the user.
                    - Maintain consistency with previous messages.

                    Before answering:
                    1. Understand the user's intent.
                    2. Identify relevant context.
                    3. Formulate the answer.
                    4. Verify that the answer addresses the question.
                    """
                }

            ] + history,
            options={
                "temperature": 0.2,
                "num_predict": 800,
                "top_p": 0.9
            }
        )

        reply = response["message"]["content"]

        print("BOT:", reply)

        # Save AI response
        save_message(
            current_chat_id,
            "assistant",
            reply
        )

        return jsonify(
            {
                "reply": reply
            }
        )

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify(
            {
                "reply": f"Error: {str(e)}"
            }
        )

# ==========================
# NEW CHAT
# ==========================

@app.route("/clear", methods=["POST"])
def clear():

    global current_chat_id

    if current_chat_id is None:
        current_chat_id = create_chat("New Chat")

    return jsonify({
        "status": "success",
        "chat_id": current_chat_id
    })
# ==========================
# GET ALL CHATS
# ==========================

@app.route("/get_chats")
@app.route("/get_chats")
def get_chats():

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.title
        FROM chats c
        WHERE EXISTS (
            SELECT 1
            FROM messages m
            WHERE m.chat_id = c.id
        )
        ORDER BY c.id DESC
    """)

    chats = cursor.fetchall()

    conn.close()

    return jsonify(chats)

# ==========================
# LOAD CHAT
# ==========================

@app.route("/load_chat/<int:chat_id>")
def load_chat(chat_id):

    history = get_chat_history(chat_id)

    return jsonify(history)

# ==========================
# DELETE CHAT
# ==========================

@app.route(
    "/delete_chat/<int:chat_id>",
    methods=["DELETE"]
)
def delete_chat(chat_id):

    conn = sqlite3.connect("chatbot.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE chat_id=?
        """,
        (chat_id,)
    )

    cursor.execute(
        """
        DELETE FROM chats
        WHERE id=?
        """,
        (chat_id,)
    )

    conn.commit()

    conn.close()

    return jsonify(
        {
            "success": True
        }
    )

# ==========================
# RUN
# ==========================

if __name__ == "__main__":

    app.run(debug=True)

