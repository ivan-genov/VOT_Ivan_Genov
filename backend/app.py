import os
import time
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "notesdb")
DB_USER = os.getenv("DB_USER", "notesuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "notessecret")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def init_db():
    # прост retry, за да изчака Postgres да стане ready
    for _ in range(30):
        try:
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS notes (
                            id SERIAL PRIMARY KEY,
                            content TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                    """)
            conn.close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("DB not ready after retries")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/notes")
def list_notes():
    init_db()
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC;")
            rows = cur.fetchall()
    conn.close()
    return jsonify([
        {"id": r[0], "content": r[1], "created_at": r[2].isoformat()}
        for r in rows
    ])

@app.post("/notes")
def add_note():
    init_db()
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return {"error": "content is required"}, 400

    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO notes(content) VALUES (%s) RETURNING id;", (content,))
            new_id = cur.fetchone()[0]
    conn.close()
    return {"id": new_id, "content": content}, 201

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
