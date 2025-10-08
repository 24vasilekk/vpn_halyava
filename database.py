import sqlite3
from datetime import datetime, timedelta
from config import TRIAL_DURATION_DAYS, MAX_DEVICES

class Database:
    def __init__(self, db_file='database.db'):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                referrer_id INTEGER,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица подписок (добавлено поле user_uuid)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vpn_key TEXT,
                user_uuid TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_trial BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица платежей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                payment_id TEXT,
                payment_method TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                selected_server INTEGER DEFAULT 1,
                selected_protocol TEXT DEFAULT 'wireguard',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.connection.commit()
    
    def add_user(self, user_id, username, referrer_id=None):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, referrer_id)
                VALUES (?, ?, ?)
            ''', (user_id, username, referrer_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def activate_trial(self, user_id, vpn_key, user_uuid):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=TRIAL_DURATION_DAYS)
        
        try:
            self.cursor.execute('''
                INSERT INTO subscriptions (user_id, vpn_key, user_uuid, start_date, end_date, is_trial, is_active)
                VALUES (?, ?, ?, ?, ?, 1, 1)
            ''', (user_id, vpn_key, user_uuid, start_date, end_date))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error activating trial: {e}")
            return False
    
    def get_active_subscription(self, user_id):
        self.cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND is_active = 1 AND end_date > ?
            ORDER BY end_date DESC LIMIT 1
        ''', (user_id, datetime.now()))
        return self.cursor.fetchone()
    
    def add_subscription(self, user_id, vpn_key, user_uuid, duration_days=30):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        try:
            self.cursor.execute('''
                INSERT INTO subscriptions (user_id, vpn_key, user_uuid, start_date, end_date, is_trial, is_active)
                VALUES (?, ?, ?, ?, ?, 0, 1)
            ''', (user_id, vpn_key, user_uuid, start_date, end_date))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding subscription: {e}")
            return False
    
    def add_payment(self, user_id, amount, payment_id, payment_method='yoomoney', status='pending'):
        try:
            self.cursor.execute('''
                INSERT INTO payments (user_id, amount, payment_id, payment_method, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, amount, payment_id, payment_method, status))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding payment: {e}")
            return False
    
    def update_payment_status(self, payment_id, status):
        try:
            self.cursor.execute('''
                UPDATE payments SET status = ? WHERE payment_id = ?
            ''', (status, payment_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error updating payment status: {e}")
            return False
    
    def get_payment(self, payment_id):
        self.cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        return self.cursor.fetchone()
    
    def update_balance(self, user_id, amount):
        try:
            self.cursor.execute('''
                UPDATE users SET balance = balance + ? WHERE user_id = ?
            ''', (amount, user_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False
    
    # ========================================
    # АДМИН ФУНКЦИИ
    # ========================================
    
    def get_all_users_count(self):
        """Получает общее количество пользователей"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        return self.cursor.fetchone()[0]
    
    def get_trial_users(self):
        """Получает всех пользователей с пробным периодом"""
        self.cursor.execute('''
            SELECT 
                u.user_id,
                u.username,
                s.start_date,
                s.end_date,
                s.is_active
            FROM users u
            JOIN subscriptions s ON u.user_id = s.user_id
            WHERE s.is_trial = 1
            ORDER BY s.end_date DESC
        ''')
        return self.cursor.fetchall()
    
    def get_paid_users(self):
        """Получает всех пользователей с платной подпиской"""
        self.cursor.execute('''
            SELECT 
                u.user_id,
                u.username,
                s.start_date,
                s.end_date,
                s.is_active
            FROM users u
            JOIN subscriptions s ON u.user_id = s.user_id
            WHERE s.is_trial = 0
            ORDER BY s.end_date DESC
        ''')
        return self.cursor.fetchall()
    
    def get_active_subscriptions_count(self):
        """Получает количество активных подписок"""
        self.cursor.execute('''
            SELECT COUNT(*) FROM subscriptions 
            WHERE is_active = 1 AND end_date > ?
        ''', (datetime.now(),))
        return self.cursor.fetchone()[0]
    
    def get_expired_subscriptions(self):
        """Получает истекшие подписки"""
        self.cursor.execute('''
            SELECT 
                u.user_id,
                u.username,
                s.user_uuid,
                s.end_date,
                s.is_trial
            FROM users u
            JOIN subscriptions s ON u.user_id = s.user_id
            WHERE s.is_active = 1 AND s.end_date < ?
        ''', (datetime.now(),))
        return self.cursor.fetchall()
    
    def deactivate_subscription(self, user_id):
        """Деактивирует подписку пользователя"""
        try:
            self.cursor.execute('''
                UPDATE subscriptions SET is_active = 0 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error deactivating subscription: {e}")
            return False
    
    def get_total_revenue(self):
        """Получает общую сумму платежей"""
        self.cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE status = 'paid'
        ''')
        return self.cursor.fetchone()[0]
    
    def get_revenue_by_method(self):
        """Получает статистику по методам оплаты"""
        self.cursor.execute('''
            SELECT 
                payment_method,
                COUNT(*) as count,
                SUM(amount) as total
            FROM payments
            WHERE status = 'paid'
            GROUP BY payment_method
        ''')
        return self.cursor.fetchall()
    
    def get_recent_payments(self, limit=10):
        """Получает последние платежи"""
        self.cursor.execute('''
            SELECT 
                p.user_id,
                u.username,
                p.amount,
                p.payment_method,
                p.status,
                p.created_at
            FROM payments p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    def get_expiring_subscriptions(self, days=3):
        """Получает подписки, которые истекают в ближайшие N дней"""
        now = datetime.now()
        future = now + timedelta(days=days)
        
        self.cursor.execute('''
            SELECT 
                u.user_id,
                u.username,
                s.end_date,
                s.is_trial
            FROM users u
            JOIN subscriptions s ON u.user_id = s.user_id
            WHERE s.is_active = 1 
              AND s.end_date > ? 
              AND s.end_date <= ?
            ORDER BY s.end_date ASC
        ''', (now, future))
        
        return self.cursor.fetchall()
    
    def get_user_preferences(self, user_id):
        """Получает настройки сервера и протокола пользователя"""
        self.cursor.execute('''
            SELECT selected_server, selected_protocol 
            FROM user_preferences 
            WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        if result:
            return result
        else:
            # По умолчанию: Сервер 1, WireGuard
            self.set_user_preferences(user_id, 1, 'wireguard')
            return (1, 'wireguard')
    
    def set_user_preferences(self, user_id, server=1, protocol='wireguard'):
        """Устанавливает настройки сервера и протокола"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (user_id, selected_server, selected_protocol)
                VALUES (?, ?, ?)
            ''', (user_id, server, protocol))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error setting preferences: {e}")
            return False

    def close(self):
        self.connection.close()