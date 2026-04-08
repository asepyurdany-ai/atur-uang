import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atur_uang.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            pool INTEGER NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT NOT NULL,
            category TEXT DEFAULT 'umum',
            date TEXT DEFAULT (date('now','localtime')),
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)
    conn.commit()
    conn.close()


def _get_balance(c, project_id, pool):
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE project_id=?", (project_id,))
    total_spent = c.fetchone()[0]
    return pool - total_spent, total_spent


def create_project(name, pool, description=""):
    conn = _conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO projects (name, pool, description) VALUES (?, ?, ?)",
            (name, pool, description)
        )
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return {
            "id": pid,
            "name": name,
            "pool": pool,
            "description": description,
            "balance": pool,
            "total_spent": 0,
        }
    except sqlite3.IntegrityError:
        conn.close()
        return None  # duplicate name


def list_projects():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT id, name, pool, description, created_at FROM projects ORDER BY id")
    rows = c.fetchall()
    result = []
    for row in rows:
        pid, name, pool, desc, created_at = row
        balance, total_spent = _get_balance(c, pid, pool)
        result.append({
            "id": pid,
            "name": name,
            "pool": pool,
            "description": desc,
            "created_at": created_at,
            "balance": balance,
            "total_spent": total_spent,
        })
    conn.close()
    return result


def _find_project(c, name):
    """Find project by exact or partial name match (case-insensitive)."""
    name_lower = name.lower().strip()
    c.execute("SELECT id, name, pool, description, created_at FROM projects")
    rows = c.fetchall()
    # exact match first
    for row in rows:
        if row[1].lower() == name_lower:
            return row
    # partial match
    for row in rows:
        if name_lower in row[1].lower():
            return row
    return None


def get_project(name):
    conn = _conn()
    c = conn.cursor()
    row = _find_project(c, name)
    if not row:
        conn.close()
        return None
    pid, pname, pool, desc, created_at = row
    balance, total_spent = _get_balance(c, pid, pool)
    conn.close()
    return {
        "id": pid,
        "name": pname,
        "pool": pool,
        "description": desc,
        "created_at": created_at,
        "balance": balance,
        "total_spent": total_spent,
    }


def add_transaction(project_name, amount, description, category="umum", date=None):
    conn = _conn()
    c = conn.cursor()
    row = _find_project(c, project_name)
    if not row:
        conn.close()
        return None
    pid, pname, pool, _, _ = row
    if date:
        c.execute(
            "INSERT INTO transactions (project_id, amount, description, category, date) VALUES (?, ?, ?, ?, ?)",
            (pid, amount, description, category, date)
        )
    else:
        c.execute(
            "INSERT INTO transactions (project_id, amount, description, category) VALUES (?, ?, ?, ?)",
            (pid, amount, description, category)
        )
    conn.commit()
    tx_id = c.lastrowid
    balance, _ = _get_balance(c, pid, pool)
    conn.close()
    return {
        "id": tx_id,
        "project_name": pname,
        "amount": amount,
        "description": description,
        "category": category,
        "date": date,
        "balance": balance,
    }


def delete_transaction(tx_id):
    conn = _conn()
    c = conn.cursor()
    # Get transaction info before deleting
    c.execute(
        "SELECT t.id, t.amount, t.description, t.project_id, p.pool, p.name "
        "FROM transactions t JOIN projects p ON t.project_id=p.id WHERE t.id=?",
        (tx_id,)
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    tid, amount, desc, pid, pool, pname = row
    c.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    balance, _ = _get_balance(c, pid, pool)
    conn.close()
    return {
        "id": tid,
        "amount": amount,
        "description": desc,
        "project_name": pname,
        "balance": balance,
    }


def get_transactions(project_name, days=None):
    conn = _conn()
    c = conn.cursor()
    row = _find_project(c, project_name)
    if not row:
        conn.close()
        return None
    pid, pname, pool, _, _ = row
    if days:
        c.execute(
            "SELECT id, amount, description, category, date, created_at "
            "FROM transactions WHERE project_id=? AND date >= date('now','localtime',?) "
            "ORDER BY date, id",
            (pid, f"-{days} days")
        )
    else:
        c.execute(
            "SELECT id, amount, description, category, date, created_at "
            "FROM transactions WHERE project_id=? ORDER BY date, id",
            (pid,)
        )
    rows = c.fetchall()
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "amount": r[1],
            "description": r[2],
            "category": r[3],
            "date": r[4],
            "created_at": r[5],
        })
    conn.close()
    return {"project_name": pname, "pool": pool, "transactions": result}


def get_summary(project_name):
    conn = _conn()
    c = conn.cursor()
    row = _find_project(c, project_name)
    if not row:
        conn.close()
        return None
    pid, pname, pool, _, _ = row
    c.execute(
        "SELECT category, SUM(amount) FROM transactions WHERE project_id=? GROUP BY category",
        (pid,)
    )
    by_category = {r[0]: r[1] for r in c.fetchall()}
    balance, total_spent = _get_balance(c, pid, pool)
    c.execute("SELECT COUNT(*) FROM transactions WHERE project_id=?", (pid,))
    tx_count = c.fetchone()[0]
    conn.close()
    return {
        "project_name": pname,
        "pool": pool,
        "total_spent": total_spent,
        "balance": balance,
        "by_category": by_category,
        "tx_count": tx_count,
    }
