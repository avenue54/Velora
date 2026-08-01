import sqlite3
from datetime import datetime, timedelta
import os

DB_NAME = os.getenv("VELORA_DB_PATH", "/app/data/velora.db")


def get_connection():
    # Создаём директорию, если путь вроде /app/data/...
    db_dir = os.path.dirname(DB_NAME)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_NAME)


# =========================
# СОЗДАНИЕ БАЗЫ
# =========================

def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        status TEXT DEFAULT 'guest',
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        devices INTEGER,
        period TEXT,
        price TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        period TEXT,
        price TEXT,
        status TEXT,
        start_date TEXT,
        end_date TEXT,
        devices_used INTEGER DEFAULT 0,
        reminded INTEGER DEFAULT 0
    )
    """)

    # Миграции для старых баз
    for sql in (
        "ALTER TABLE subscriptions ADD COLUMN end_date TEXT",
        "ALTER TABLE subscriptions ADD COLUMN devices_used INTEGER DEFAULT 0",
        "ALTER TABLE subscriptions ADD COLUMN reminded INTEGER DEFAULT 0",
    ):
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass

    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            """
            INSERT INTO plans (name, description, devices, period, price)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Start", "Для знакомства с VELORA", 2, "1 месяц", "69 ₽"),
                ("Start", "Для знакомства с VELORA", 2, "3 месяца", "149 ₽"),
                ("Plus", "Популярный тариф", 5, "1 месяц", "129 ₽"),
                ("Plus", "Популярный тариф", 5, "3 месяца", "349 ₽"),
                ("Pro", "Максимальные возможности", 10, "1 месяц", "199 ₽"),
                ("Pro", "Максимальные возможности", 10, "3 месяца", "499 ₽"),
            ],
        )

    conn.commit()
    conn.close()


# =========================
# ПОЛЬЗОВАТЕЛИ
# =========================

def add_user(telegram_id, username, first_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (telegram_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            telegram_id,
            username,
            first_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_id(telegram_id):
    user = get_user(telegram_id)
    if user:
        return user[0]
    return None


# =========================
# ТАРИФЫ
# =========================

def get_plans():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE active = 1")
    plans = cursor.fetchall()
    conn.close()
    return plans


def get_plans_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM plans WHERE name = ? AND active = 1",
        (name,),
    )
    plans = cursor.fetchall()
    conn.close()
    return plans


def get_plan_by_period(plan_name, period):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM plans
        WHERE name = ? AND period = ? AND active = 1
        """,
        (plan_name, period),
    )
    plan = cursor.fetchone()
    conn.close()
    return plan


# =========================
# ПОДПИСКИ
# =========================

def create_subscription(telegram_id, plan, period, price):
    user_id = get_user_id(telegram_id)
    if not user_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO subscriptions
        (user_id, plan, period, price, status, start_date, end_date, devices_used, reminded)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, plan, period, price, "pending", None, None, 0, 0),
    )
    conn.commit()
    conn.close()
    return True


def get_user_subscription(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            subscriptions.plan,
            subscriptions.period,
            subscriptions.price,
            subscriptions.status,
            subscriptions.start_date,
            subscriptions.end_date,
            subscriptions.devices_used
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE users.telegram_id = ?
        ORDER BY subscriptions.id DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    subscription = cursor.fetchone()
    conn.close()
    return subscription


def activate_subscription(subscription_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT period FROM subscriptions WHERE id = ?",
        (subscription_id,),
    )
    data = cursor.fetchone()
    if not data:
        conn.close()
        return False

    period = data[0]
    start_date = datetime.now()

    if "3 месяца" in period:
        end_date = start_date + timedelta(days=90)
    else:
        end_date = start_date + timedelta(days=30)

    cursor.execute(
        """
        UPDATE subscriptions
        SET status = 'active',
            start_date = ?,
            end_date = ?,
            reminded = 0
        WHERE id = ?
        """,
        (
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date.strftime("%Y-%m-%d %H:%M:%S"),
            subscription_id,
        ),
    )
    conn.commit()
    conn.close()
    return True


def update_subscription_status(subscription_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE subscriptions SET status = ? WHERE id = ?",
        (status, subscription_id),
    )
    conn.commit()
    conn.close()


# =========================
# АДМИН
# =========================

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    conn.close()
    return data


def get_all_subscriptions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            subscriptions.id,
            users.telegram_id,
            subscriptions.plan,
            subscriptions.period,
            subscriptions.price,
            subscriptions.status
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        ORDER BY subscriptions.id DESC
        """
    )
    subscriptions = cursor.fetchall()
    conn.close()
    return subscriptions


def get_subscriptions():
    """Pending-заявки для админки."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            subscriptions.id,
            users.first_name,
            users.telegram_id,
            subscriptions.plan,
            subscriptions.period,
            subscriptions.price,
            subscriptions.status,
            subscriptions.start_date
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE subscriptions.status = 'pending'
        ORDER BY subscriptions.id DESC
        """
    )
    data = cursor.fetchall()
    conn.close()
    return data


def get_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM subscriptions")
    subscriptions = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
    )
    active = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE status = 'pending'"
    )
    pending = cursor.fetchone()[0]

    conn.close()
    return {
        "users": users,
        "subscriptions": subscriptions,
        "active": active,
        "pending": pending,
    }


# =========================
# ПРОФИЛЬ
# =========================

def get_profile(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            users.telegram_id,
            users.first_name,
            users.created_at,
            subscriptions.plan,
            subscriptions.period,
            subscriptions.price,
            subscriptions.status,
            subscriptions.start_date,
            subscriptions.end_date,
            subscriptions.devices_used
        FROM users
        LEFT JOIN subscriptions ON users.id = subscriptions.user_id
        WHERE users.telegram_id = ?
        ORDER BY
            CASE subscriptions.status
                WHEN 'active' THEN 1
                WHEN 'pending' THEN 2
                WHEN 'rejected' THEN 3
                ELSE 4
            END,
            subscriptions.id DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    profile = cursor.fetchone()
    conn.close()
    return profile


# =========================
# УВЕДОМЛЕНИЯ / РАССЫЛКА
# =========================

def get_all_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]


def get_subscription_user_telegram_id(subscription_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT users.telegram_id
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE subscriptions.id = ?
        """,
        (subscription_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_expiring_subscriptions(hours=48):
    """
    Активные подписки, истекающие в ближайшие hours часов,
    по которым ещё не отправляли напоминание.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    deadline = now + timedelta(hours=hours)

    cursor.execute(
        """
        SELECT
            subscriptions.id,
            users.telegram_id,
            subscriptions.plan,
            subscriptions.period,
            subscriptions.end_date
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE subscriptions.status = 'active'
          AND subscriptions.end_date IS NOT NULL
          AND COALESCE(subscriptions.reminded, 0) = 0
          AND subscriptions.end_date > ?
          AND subscriptions.end_date <= ?
        """,
        (
            now.strftime("%Y-%m-%d %H:%M:%S"),
            deadline.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_subscription_reminded(subscription_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE subscriptions SET reminded = 1 WHERE id = ?",
        (subscription_id,),
    )
    conn.commit()
    conn.close()
