import sqlite3
from config import DB_PATH
from datetime import datetime


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            joined_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            validity_days INTEGER NOT NULL,
            channel_links TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            utr_number TEXT UNIQUE NOT NULL,
            screenshot_file_id TEXT,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT,
            FOREIGN KEY (plan_id) REFERENCES plans(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()


# ─────────────────── USER ───────────────────

def add_user(telegram_id: int, username: str, full_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (telegram_id, username, full_name)
        VALUES (?, ?, ?)
    """, (telegram_id, username or "", full_name or ""))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_today_user_count():
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (f"{today}%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ─────────────────── PLANS ───────────────────

def add_plan(name: str, price: float, validity_days: int, channel_links: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plans (name, price, validity_days, channel_links)
        VALUES (?, ?, ?, ?)
    """, (name, price, validity_days, channel_links))
    conn.commit()
    plan_id = cursor.lastrowid
    conn.close()
    return plan_id


def get_all_plans():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans ORDER BY price ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_plan_by_id(plan_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def delete_plan(plan_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def update_plan(plan_id: int, name: str, price: float, validity_days: int, channel_links: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE plans SET name=?, price=?, validity_days=?, channel_links=?
        WHERE id=?
    """, (name, price, validity_days, channel_links, plan_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_plan_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ─────────────────── PAYMENTS ───────────────────

def add_payment(telegram_id: int, plan_id: int, utr_number: str, screenshot_file_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO payments (telegram_id, plan_id, utr_number, screenshot_file_id)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, plan_id, utr_number, screenshot_file_id))
        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()
        return payment_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_payment_by_id(payment_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_payment_status(payment_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payments SET status=?, reviewed_at=datetime('now')
        WHERE id=?
    """, (status, payment_id))
    conn.commit()
    conn.close()


def utr_exists(utr_number: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM payments WHERE utr_number = ?", (utr_number,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_payment_counts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) as rejected
        FROM payments
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {"pending": 0, "approved": 0, "rejected": 0}


# ─────────────────── SETTINGS ───────────────────

def set_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_setting(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None
