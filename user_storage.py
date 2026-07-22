import sqlite3
import json
from datetime import datetime

DB_PATH = "user_data.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users
           (user_id INTEGER PRIMARY KEY, telegram_id INTEGER, settings TEXT, created_at TEXT)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS portfolio
           (id INTEGER PRIMARY KEY, user_id INTEGER, coin TEXT, amount REAL, buy_price REAL, 
            buy_date TEXT, status TEXT)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS alerts
           (id INTEGER PRIMARY KEY, user_id INTEGER, coin TEXT, condition TEXT, threshold REAL, 
            active INTEGER, created_at TEXT)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS reports_history
           (id INTEGER PRIMARY KEY, user_id INTEGER, coin TEXT, report TEXT, created_at TEXT)"""
    )
    return conn


def create_user(telegram_id, risk_level="medium"):
    """Создать профиль пользователя"""
    settings = {
        "risk_level": risk_level,
        "tracked_coins": ["SOL"],
        "notifications_enabled": True
    }
    
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, settings, created_at) VALUES (?, ?, ?)",
            (telegram_id, json.dumps(settings), datetime.now().isoformat())
        )


def get_user_settings(telegram_id):
    """Получить настройки пользователя"""
    with _get_conn() as conn:
        cur = conn.execute("SELECT settings FROM users WHERE telegram_id=?", (telegram_id,))
        result = cur.fetchone()
        if result:
            return json.loads(result[0])
    return None


def update_user_settings(telegram_id, settings):
    """Обновить настройки пользователя"""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE users SET settings=? WHERE telegram_id=?",
            (json.dumps(settings), telegram_id)
        )


def add_portfolio_position(telegram_id, coin, amount, buy_price):
    """Добавить позицию в портфель"""
    create_user(telegram_id)
    
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()[0]
        conn.execute(
            "INSERT INTO portfolio (user_id, coin, amount, buy_price, buy_date, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, coin.upper(), amount, buy_price, datetime.now().isoformat(), "open")
        )


def get_portfolio(telegram_id):
    """Получить портфель пользователя"""
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
        if not user_id:
            return []
        
        cur = conn.execute(
            "SELECT coin, amount, buy_price, buy_date FROM portfolio WHERE user_id=? AND status='open'",
            (user_id[0],)
        )
        return cur.fetchall()


def close_position(telegram_id, coin, sell_price):
    """Закрыть позицию в портфеле"""
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()[0]
        conn.execute(
            "UPDATE portfolio SET status='closed' WHERE user_id=? AND coin=?",
            (user_id, coin.upper())
        )


def add_alert(telegram_id, coin, condition, threshold):
    """Добавить alert (condition: 'above' или 'below')"""
    create_user(telegram_id)
    
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()[0]
        conn.execute(
            "INSERT INTO alerts (user_id, coin, condition, threshold, active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, coin.upper(), condition, threshold, 1, datetime.now().isoformat())
        )


def get_active_alerts(telegram_id):
    """Получить активные alerts"""
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
        if not user_id:
            return []
        
        cur = conn.execute(
            "SELECT id, coin, condition, threshold FROM alerts WHERE user_id=? AND active=1",
            (user_id[0],)
        )
        return cur.fetchall()


def disable_alert(alert_id):
    """Отключить alert"""
    with _get_conn() as conn:
        conn.execute("UPDATE alerts SET active=0 WHERE id=?", (alert_id,))


def save_report(telegram_id, coin, report_text):
    """Сохранить отчёт в историю"""
    create_user(telegram_id)
    
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()[0]
        conn.execute(
            "INSERT INTO reports_history (user_id, coin, report, created_at) VALUES (?, ?, ?, ?)",
            (user_id, coin.upper(), report_text, datetime.now().isoformat())
        )


def get_reports_history(telegram_id, coin=None, limit=10):
    """Получить историю отчётов"""
    with _get_conn() as conn:
        user_id = conn.execute("SELECT rowid FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
        if not user_id:
            return []
        
        if coin:
            cur = conn.execute(
                "SELECT coin, report, created_at FROM reports_history WHERE user_id=? AND coin=? ORDER BY created_at DESC LIMIT ?",
                (user_id[0], coin.upper(), limit)
            )
        else:
            cur = conn.execute(
                "SELECT coin, report, created_at FROM reports_history WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id[0], limit)
            )
        return cur.fetchall()
