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
        
        # Таблица подписок
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vpn_key TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_trial BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица платежей (обновленная)
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
    
    def activate_trial(self, user_id, vpn_key):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=TRIAL_DURATION_DAYS)
        
        try:
            self.cursor.execute('''
                INSERT INTO subscriptions (user_id, vpn_key, start_date, end_date, is_trial, is_active)
                VALUES (?, ?, ?, ?, 1, 1)
            ''', (user_id, vpn_key, start_date, end_date))
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
    
    def add_subscription(self, user_id, vpn_key, duration_days=30):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        try:
            self.cursor.execute('''
                INSERT INTO subscriptions (user_id, vpn_key, start_date, end_date, is_trial, is_active)
                VALUES (?, ?, ?, ?, 0, 1)
            ''', (user_id, vpn_key, start_date, end_date))
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
    
    def close(self):
        self.connection.close()