import psycopg2
import psycopg2.extras
from config import CONFIG


# ---------------- DB CONNECTION ---------------- #
def get_connection():
    return psycopg2.connect(
        host=CONFIG["DB_HOST"],
        database=CONFIG["DB_NAME"],
        user=CONFIG["DB_USER"],
        password=CONFIG["DB_PASSWORD"]
    )


# ---------------- USER HANDLING ---------------- #
def get_or_create_user(username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, password FROM users WHERE username=%s", (username,))
    row = cur.fetchone()

    if row:
        user_id, stored_pass = row

        if stored_pass != password:
            cur.close()
            conn.close()
            return None, "WRONG_PASSWORD"

        cur.close()
        conn.close()
        return user_id, "LOGIN_SUCCESS"

    # New user
    cur.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
        (username, password)
    )
    user_id = cur.fetchone()[0]
    conn.commit()

    cur.execute("INSERT INTO user_memory (user_id, memory) VALUES (%s, '{}'::jsonb)", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    return user_id, "NEW_USER"



# ---------------- CHAT HISTORY ---------------- #
def add_history(user_id, role, content):
    """Store each chat message in PostgreSQL."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (user_id, role, content) VALUES (%s, %s, %s)",
        (user_id, role, content)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_chat_history(user_id, limit=20):
    """Fetch last messages for AI context."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(
        "SELECT role, content FROM messages WHERE user_id=%s ORDER BY id DESC LIMIT %s",
        (user_id, limit)
    )

    rows = cur.fetchall()[::-1]  # oldest → new

    cur.close()
    conn.close()

    return [{"role": r["role"], "content": r["content"]} for r in rows]


# ---------------- USER MEMORY (long-term) ---------------- #
def load_memory(user_id):
    """Load user's long-term memory (JSONB)."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT memory FROM user_memory WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row["memory"] if row else {}


def update_memory(user_id, new_data: dict):
    """Merge new memory fields into existing JSONB."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE user_memory
        SET memory = memory || %s::jsonb
        WHERE user_id = %s
    """, (json.dumps(new_data), user_id))

    conn.commit()
    cur.close()
    conn.close()


# ---------------- NOTES ---------------- #
def add_note_db(user_id, note):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO notes (user_id, note) VALUES (%s, %s)", (user_id, note))
    conn.commit()

    cur.close()
    conn.close()


def get_notes_db(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT note FROM notes WHERE user_id=%s ORDER BY id DESC", (user_id,))
    notes = [row["note"] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return notes


def delete_note_db(user_id, note_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id=%s AND user_id=%s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()


def clear_notes_db(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def update_note_db(user_id, note_id, new_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE notes SET note=%s WHERE id=%s AND user_id=%s",
        (new_text, note_id, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_notes_with_ids_db(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, note FROM notes WHERE user_id=%s ORDER BY id ASC", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def pin_note_db(user_id, note_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notes SET pinned=TRUE WHERE id=%s AND user_id=%s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()


def unpin_note_db(user_id, note_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notes SET pinned=FALSE WHERE id=%s AND user_id=%s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()


def mark_note_done_db(user_id, note_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notes SET done=TRUE WHERE id=%s AND user_id=%s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()


def search_notes_db(user_id, keyword):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, note FROM notes WHERE user_id=%s AND LOWER(note) LIKE %s",
                (user_id, f"%{keyword.lower()}%"))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_pinned_notes_db(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, note FROM notes WHERE user_id=%s AND pinned=TRUE", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_done_notes_db(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, note FROM notes WHERE user_id=%s AND done=TRUE", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ---------------- USER MEMORY (long-term) ---------------- #
def load_user_memory(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT memory FROM user_memory WHERE user_id=%s", (user_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    return row["memory"] if row and row["memory"] else {}


def update_user_memory(user_id, key, value):
    """Store a single memory field like {"birthday": "my birthday is feb 16"}"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE user_memory SET memory = jsonb_set(memory, %s, %s, true) WHERE user_id=%s",
        (f"{{{key}}}", json.dumps(value), user_id)
    )

    conn.commit()
    cur.close()
    conn.close()


def delete_memory_key(user_id, key):
    """Delete a memory entry."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE user_memory SET memory = memory - %s WHERE user_id=%s",
        (key, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()
