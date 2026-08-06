import sqlite3
from datetime import datetime, timedelta
import os
import hashlib
import secrets
import string

DB_NAME = "/app/data/velora.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================
# СОЗДАНИЕ БАЗЫ
# =========================

def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    # Пользователи
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

    # Тарифы
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

    # Подписки
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
        devices_used INTEGER DEFAULT 0
    )
    """)

    # Миграция старой базы
    try:
        cursor.execute(
            """
            ALTER TABLE subscriptions
            ADD COLUMN end_date TEXT
            """
        )
    except Exception:
        pass

    try:
        cursor.execute(
            """
            ALTER TABLE subscriptions
            ADD COLUMN devices_used INTEGER DEFAULT 0
            """
        )
    except Exception:
        pass

    try:
        cursor.execute(
            """
            ALTER TABLE subscriptions
            ADD COLUMN reminded INTEGER DEFAULT 0
            """
        )
    except Exception:
        pass

    # Платежи
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        plan TEXT,
        period TEXT,
        amount TEXT,
        status TEXT DEFAULT 'pending',
        provider TEXT,
        provider_payment_id TEXT,
        created_at TEXT,
        paid_at TEXT
    )
    """)

    # VPN конфигурации WireGuard
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vpn_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        private_key TEXT,
        public_key TEXT,
        vpn_ip TEXT,
        created_at TEXT
    )
    """)


    # --- referral / promo / admin ---
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN bonus_days INTEGER DEFAULT 0")
    except Exception:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS promo_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent INTEGER DEFAULT 0,
        bonus_days INTEGER DEFAULT 0,
        max_uses INTEGER DEFAULT 0,
        used_count INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TEXT,
        expires_at TEXT
    )
    """)
    try:
        cursor.execute("ALTER TABLE promo_codes ADD COLUMN expires_at TEXT")
    except Exception:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS promo_uses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        promo_id INTEGER,
        telegram_id INTEGER,
        used_at TEXT,
        UNIQUE(promo_id, telegram_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referral_rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_tg INTEGER NOT NULL,
        buyer_tg INTEGER NOT NULL,
        days INTEGER NOT NULL,
        payment_id INTEGER,
        created_at TEXT,
        UNIQUE(buyer_tg, payment_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS device_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        label TEXT,
        created_at TEXT
    )
    """)

    # Добавление тарифов
    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            """
            INSERT INTO plans
            (name, description, devices, period, price)
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

def _gen_referral_code(telegram_id: int) -> str:
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"VL{telegram_id % 100000}{suffix}"


def add_user(telegram_id, username, first_name, referred_by=None):
    conn = get_connection()
    cursor = conn.cursor()
    code = _gen_referral_code(telegram_id)
    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (telegram_id, username, first_name, created_at, referral_code, referred_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            username,
            first_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            code,
            referred_by,
        ),
    )
    # если пользователь уже был — дописать referral_code если пустой
    cursor.execute(
        "SELECT referral_code FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cursor.fetchone()
    if row and not row[0]:
        cursor.execute(
            "UPDATE users SET referral_code = ? WHERE telegram_id = ?",
            (code, telegram_id),
        )
    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
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
    cursor.execute(
        """
        SELECT *
        FROM plans
        WHERE active = 1
        """
    )
    plans = cursor.fetchall()
    conn.close()
    return plans


def get_plans_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM plans
        WHERE name = ?
        AND active = 1
        """,
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
        SELECT *
        FROM plans
        WHERE name = ?
        AND period = ?
        AND active = 1
        """,
        (plan_name, period),
    )
    plan = cursor.fetchone()
    conn.close()
    return plan


# =========================
# ПОДПИСКИ
# =========================


def get_device_limit(plan_name: str) -> int:
    """Лимит устройств по имени тарифа из plans, иначе дефолт."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT devices FROM plans
        WHERE name = ? AND active = 1
        ORDER BY id LIMIT 1
        """,
        (plan_name,),
    )
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return int(row[0])
    defaults = {"Start": 2, "Plus": 5, "Pro": 10}
    return defaults.get(plan_name, 1)

def create_subscription(telegram_id, plan, period, price):
    user_id = get_user_id(telegram_id)
    if not user_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO subscriptions
        (user_id, plan, period, price, status, start_date, end_date, devices_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, plan, period, price, "pending", None, None, 0),
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


# =========================
# АКТИВАЦИЯ ПОДПИСКИ
# =========================

def activate_subscription(subscription_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT period
        FROM subscriptions
        WHERE id = ?
        """,
        (subscription_id,),
    )
    data = cursor.fetchone()

    if not data:
        conn.close()
        return False

    period = data[0]
    start_date = datetime.now()

    if "1 месяц" in period:
        end_date = start_date + timedelta(days=30)
    elif "3 месяца" in period:
        end_date = start_date + timedelta(days=90)
    else:
        end_date = start_date + timedelta(days=30)

    # бонусные дни с промокода / рефералки (users.bonus_days)
    cursor.execute(
        """
        SELECT users.telegram_id, COALESCE(users.bonus_days, 0)
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE subscriptions.id = ?
        """,
        (subscription_id,),
    )
    urow = cursor.fetchone()
    extra = 0
    tg_id = None
    if urow:
        tg_id, extra = urow[0], int(urow[1] or 0)
    if extra > 0:
        end_date = end_date + timedelta(days=extra)
        cursor.execute(
            "UPDATE users SET bonus_days = 0 WHERE telegram_id = ?",
            (tg_id,),
        )

    cursor.execute(
        """
        UPDATE subscriptions
        SET
            status = 'active',
            start_date = ?,
            end_date = ?
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
        """
        UPDATE subscriptions
        SET status = ?
        WHERE id = ?
        """,
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
# РАССЫЛКА / УВЕДОМЛЕНИЯ
# =========================

def get_all_telegram_ids():
    """Все telegram_id пользователей для рассылки."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]


def get_subscription_user_telegram_id(subscription_id):
    """Telegram ID владельца подписки."""
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
    Активные подписки, истекающие в ближайшие hours часов.
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
    try:
        cursor.execute(
            "UPDATE subscriptions SET reminded = 1 WHERE id = ?",
            (subscription_id,),
        )
        conn.commit()
    except Exception:
        pass
    conn.close()


# =========================
# ПЛАТЕЖИ (ЗАКАЗЫ)
# =========================

def create_payment(
    telegram_id: int,
    plan: str,
    period: str,
    amount: str,
    provider: str = "platega",
):
    """Создать платёж (заказ) со статусом pending. Возвращает payment_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO payments
        (telegram_id, plan, period, amount, status, provider, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """,
        (
            telegram_id,
            plan,
            period,
            amount,
            provider,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return payment_id


def get_payment(payment_id: int):
    """Получить платёж по id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_last_payment(telegram_id: int):
    """Последний платёж пользователя."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM payments
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def update_payment_status(payment_id: int, status: str, provider_payment_id=None):
    """Обновить статус платежа. При status='paid' ставит paid_at."""
    conn = get_connection()
    cursor = conn.cursor()
    if status == "paid":
        cursor.execute(
            """
            UPDATE payments
            SET status = ?,
                provider_payment_id = COALESCE(?, provider_payment_id),
                paid_at = ?
            WHERE id = ?
            """,
            (
                status,
                provider_payment_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                payment_id,
            ),
        )
    else:
        cursor.execute(
            """
            UPDATE payments
            SET status = ?,
                provider_payment_id = COALESCE(?, provider_payment_id)
            WHERE id = ?
            """,
            (status, provider_payment_id, payment_id),
        )
    conn.commit()
    conn.close()



def get_payment_by_provider_id(provider_payment_id: str):
    """Найти платёж по ID транзакции Platega."""
    if not provider_payment_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM payments
        WHERE provider_payment_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (provider_payment_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row

# =========================
# VPN
# =========================

def save_vpn_config(telegram_id, private_key, public_key, vpn_ip):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO vpn_configs
        (telegram_id, private_key, public_key, vpn_ip, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            private_key,
            public_key,
            vpn_ip,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()


def get_vpn_config(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM vpn_configs
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    )

    data = cursor.fetchone()
    conn.close()

    return data


# =========================
# ADMIN SETTINGS
# =========================

def admin_get(key: str, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def admin_set(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO admin_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    conn.commit()
    conn.close()


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return digest, salt


def set_admin_password(password: str) -> None:
    digest, salt = hash_password(password)
    admin_set("password_hash", digest)
    admin_set("password_salt", salt)


def check_admin_password(password: str) -> bool:
    h = admin_get("password_hash")
    s = admin_get("password_salt")
    if not h or not s:
        return False
    digest, _ = hash_password(password, s)
    return digest == h


def is_admin_password_set() -> bool:
    return bool(admin_get("password_hash"))


def get_admin_display_name() -> str:
    return admin_get("display_name") or "Админ"


def set_admin_display_name(name: str) -> None:
    admin_set("display_name", name.strip()[:64])


# =========================
# REFERRALS & PROMO
# =========================

def get_referral_code(telegram_id: int) -> str | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT referral_code FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    if row and row[0]:
        conn.close()
        return row[0]
    # generate if missing
    code = _gen_referral_code(telegram_id)
    cursor.execute(
        "UPDATE users SET referral_code = ? WHERE telegram_id = ?",
        (code, telegram_id),
    )
    conn.commit()
    conn.close()
    return code


def get_user_by_referral_code(code: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT telegram_id, id FROM users WHERE referral_code = ?",
        (code.strip().upper(),),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def set_referred_by(telegram_id: int, referrer_tg_id: int) -> bool:
    """Привязать реферера только если ещё не привязан и это не сам себя."""
    if telegram_id == referrer_tg_id:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    if row[0]:
        conn.close()
        return False
    cursor.execute(
        "UPDATE users SET referred_by = ? WHERE telegram_id = ?",
        (referrer_tg_id, telegram_id),
    )
    conn.commit()
    conn.close()
    return True


def count_referrals(telegram_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by = ?",
        (telegram_id,),
    )
    n = cursor.fetchone()[0]
    conn.close()
    return n


def create_promo_code(
    code: str,
    bonus_days: int = 0,
    expires_in_days: int = 0,
    discount_percent: int = 0,
    max_uses: int = 0,
) -> bool:
    """
    expires_in_days: 0 = бессрочный, иначе промо действует N дней с момента создания.
    """
    conn = get_connection()
    cursor = conn.cursor()
    created = datetime.now()
    expires_at = None
    if int(expires_in_days) > 0:
        expires_at = (created + timedelta(days=int(expires_in_days))).strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            """
            INSERT INTO promo_codes
            (code, discount_percent, bonus_days, max_uses, used_count, active, created_at, expires_at)
            VALUES (?, ?, ?, ?, 0, 1, ?, ?)
            """,
            (
                code.strip().upper(),
                int(discount_percent),
                int(bonus_days),
                int(max_uses),
                created.strftime("%Y-%m-%d %H:%M:%S"),
                expires_at,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def get_promo(code: str):
    """
    Returns tuple:
    id, code, discount_percent, bonus_days, max_uses, used_count, active, expires_at
    or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, code, discount_percent, bonus_days, max_uses, used_count, active, expires_at
        FROM promo_codes WHERE code = ?
        """,
        (code.strip().upper(),),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def is_promo_valid(promo_row) -> tuple[bool, str]:
    """promo_row from get_promo. Returns (ok, error_message)."""
    if not promo_row:
        return False, "Промокод не найден."
    # indices: 0 id, 1 code, 2 disc, 3 days, 4 max, 5 used, 6 active, 7 expires
    if len(promo_row) < 7 or not promo_row[6]:
        return False, "Промокод неактивен."
    expires = promo_row[7] if len(promo_row) > 7 else None
    if expires:
        try:
            exp = datetime.strptime(expires, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > exp:
                return False, "Срок действия промокода истёк."
        except ValueError:
            pass
    max_uses, used = promo_row[4], promo_row[5]
    if max_uses and used >= max_uses:
        return False, "Лимит использований исчерпан."
    if int(promo_row[3] or 0) <= 0:
        return False, "Промокод не даёт дней."
    return True, ""


def list_promo_codes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, code, discount_percent, bonus_days, max_uses, used_count, active, expires_at
        FROM promo_codes ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def apply_promo_use(promo_id: int, telegram_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT max_uses, used_count, active FROM promo_codes WHERE id = ?",
        (promo_id,),
    )
    row = cursor.fetchone()
    if not row or not row[2]:
        conn.close()
        return False
    max_uses, used_count = row[0], row[1]
    if max_uses and used_count >= max_uses:
        conn.close()
        return False
    try:
        cursor.execute(
            "INSERT INTO promo_uses (promo_id, telegram_id, used_at) VALUES (?, ?, ?)",
            (promo_id, telegram_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        cursor.execute(
            "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?",
            (promo_id,),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def deactivate_promo(code: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE promo_codes SET active = 0 WHERE code = ?",
        (code.strip().upper(),),
    )
    conn.commit()
    conn.close()


# =========================
# DEVICE SLOTS
# =========================

def count_device_slots(telegram_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM device_slots WHERE telegram_id = ?",
        (telegram_id,),
    )
    n = cursor.fetchone()[0]
    conn.close()
    return n


def list_device_slots(telegram_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, label, created_at FROM device_slots WHERE telegram_id = ? ORDER BY id",
        (telegram_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_device_slot(telegram_id: int, label: str, max_devices: int) -> tuple[bool, str]:
    used = count_device_slots(telegram_id)
    if used >= max_devices:
        return False, f"Лимит устройств тарифа: {max_devices}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO device_slots (telegram_id, label, created_at) VALUES (?, ?, ?)",
        (telegram_id, label[:40], datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    # sync devices_used on subscription
    cursor.execute(
        """
        UPDATE subscriptions SET devices_used = ?
        WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
          AND status = 'active'
        """,
        (used + 1, telegram_id),
    )
    conn.commit()
    conn.close()
    return True, "ok"


def remove_device_slot(slot_id: int, telegram_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM device_slots WHERE id = ? AND telegram_id = ?",
        (slot_id, telegram_id),
    )
    ok = cursor.rowcount > 0
    if ok:
        used = count_device_slots(telegram_id)
        cursor.execute(
            """
            UPDATE subscriptions SET devices_used = ?
            WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
              AND status = 'active'
            """,
            (used, telegram_id),
        )
    conn.commit()
    conn.close()
    return ok

def get_referred_by(telegram_id: int):
    """telegram_id реферера или None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT referred_by FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return int(row[0])
    return None


def extend_active_subscription_days(telegram_id: int, days: int) -> tuple[bool, str]:
    """
    Продлевает активную подписку на days дней.
    Если подписки нет — копит bonus_days на users.
    Returns (ok, message).
    """
    if days <= 0:
        return False, "days<=0"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT subscriptions.id, subscriptions.end_date
        FROM subscriptions
        JOIN users ON subscriptions.user_id = users.id
        WHERE users.telegram_id = ?
          AND subscriptions.status = 'active'
        ORDER BY subscriptions.id DESC
        LIMIT 1
        """,
        (telegram_id,),
    )
    row = cursor.fetchone()
    if row:
        sub_id, end_raw = row
        try:
            end = datetime.strptime(end_raw, "%Y-%m-%d %H:%M:%S") if end_raw else datetime.now()
        except ValueError:
            end = datetime.now()
        if end < datetime.now():
            end = datetime.now()
        new_end = end + timedelta(days=days)
        cursor.execute(
            "UPDATE subscriptions SET end_date = ? WHERE id = ?",
            (new_end.strftime("%Y-%m-%d %H:%M:%S"), sub_id),
        )
        conn.commit()
        conn.close()
        return True, new_end.strftime("%Y-%m-%d %H:%M:%S")

    # нет активной — копим
    cursor.execute(
        "UPDATE users SET bonus_days = COALESCE(bonus_days, 0) + ? WHERE telegram_id = ?",
        (days, telegram_id),
    )
    conn.commit()
    conn.close()
    return True, "stored_bonus"


def was_referral_rewarded(buyer_tg: int, payment_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM referral_rewards WHERE buyer_tg = ? AND payment_id = ?",
        (buyer_tg, payment_id),
    )
    ok = cursor.fetchone() is not None
    conn.close()
    return ok


def record_referral_reward(referrer_tg: int, buyer_tg: int, days: int, payment_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO referral_rewards (referrer_tg, buyer_tg, days, payment_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                referrer_tg,
                buyer_tg,
                days,
                payment_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def grant_referral_bonus_for_payment(buyer_tg: int, payment_id: int, days: int = 3) -> dict:
    """
    Если buyer пришёл по рефералке — начислить referrer +days.
    Один payment_id / buyer — один раз.
    """
    result = {"granted": False, "referrer": None, "new_end": None, "reason": ""}
    referrer = get_referred_by(buyer_tg)
    if not referrer:
        result["reason"] = "no_referrer"
        return result
    if was_referral_rewarded(buyer_tg, payment_id):
        result["reason"] = "already"
        result["referrer"] = referrer
        return result
    if not record_referral_reward(referrer, buyer_tg, days, payment_id):
        result["reason"] = "duplicate"
        result["referrer"] = referrer
        return result
    ok, info = extend_active_subscription_days(referrer, days)
    result["granted"] = ok
    result["referrer"] = referrer
    result["new_end"] = info
    result["reason"] = "ok" if ok else "extend_failed"
    return result

def get_referral_reward_by_payment(payment_id: int):
    """(referrer_tg, buyer_tg, days, created_at) or None"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT referrer_tg, buyer_tg, days, created_at
        FROM referral_rewards
        WHERE payment_id = ?
        ORDER BY id DESC LIMIT 1
        """,
        (payment_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row
