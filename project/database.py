import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Manages SQLite database connections and operations for the finance tracker."""
    
    def __init__(self, db_path: str = 'finance.db'):
        self.db_path = db_path
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for database operations."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_single(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return a single result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the new row ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def init_database(self):
        """Initialize the database with all required tables and indexes."""
        self.logger.info("Initializing database...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Transactions table
            cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                category TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
                description TEXT,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )''')
            
            # Budgets table
            cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
                month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
                year INTEGER NOT NULL CHECK (year >= 2020),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, category, month, year)
            )''')
            
            # Categories table for better category management
            cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense', 'both')),
                description TEXT,
                color TEXT DEFAULT '#6366f1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # User preferences table
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                currency TEXT DEFAULT 'USD',
                date_format TEXT DEFAULT '%Y-%m-%d',
                theme TEXT DEFAULT 'light',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )''')
            
            # Create indexes for better performance
            self._create_indexes(cursor)
            
            # Insert default categories
            self._insert_default_categories(cursor)
            
            conn.commit()
            self.logger.info("Database initialization completed successfully")
    
    def _create_indexes(self, cursor):
        """Create database indexes for better query performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_budgets_month_year ON budgets(month, year)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def _insert_default_categories(self, cursor):
        """Insert default income and expense categories."""
        categories = [
            # Income categories
            ('Salary', 'income', 'Regular employment income', '#10b981'),
            ('Freelance', 'income', 'Freelance work income', '#059669'),
            ('Investment', 'income', 'Investment returns', '#0d9488'),
            ('Business', 'income', 'Business income', '#0891b2'),
            ('Other Income', 'income', 'Other sources of income', '#3b82f6'),
            
            # Expense categories
            ('Food & Dining', 'expense', 'Restaurants, groceries, etc.', '#ef4444'),
            ('Transportation', 'expense', 'Gas, public transit, car maintenance', '#f97316'),
            ('Shopping', 'expense', 'Clothes, electronics, misc shopping', '#f59e0b'),
            ('Entertainment', 'expense', 'Movies, games, hobbies', '#eab308'),
            ('Bills & Utilities', 'expense', 'Electricity, water, internet, phone', '#84cc16'),
            ('Healthcare', 'expense', 'Medical expenses, insurance', '#22c55e'),
            ('Education', 'expense', 'Books, courses, tuition', '#06b6d4'),
            ('Travel', 'expense', 'Vacation, business travel', '#3b82f6'),
            ('Housing', 'expense', 'Rent, mortgage, home maintenance', '#6366f1'),
            ('Insurance', 'expense', 'Car, home, life insurance', '#8b5cf6'),
            ('Gifts & Donations', 'expense', 'Gifts, charity donations', '#a855f7'),
            ('Personal Care', 'expense', 'Haircuts, cosmetics, gym', '#ec4899'),
            ('Other Expenses', 'expense', 'Miscellaneous expenses', '#6b7280')
        ]
        
        for name, cat_type, description, color in categories:
            cursor.execute('''INSERT OR IGNORE INTO categories 
                            (name, type, description, color) VALUES (?, ?, ?, ?)''',
                          (name, cat_type, description, color))
    
    def backup_database(self, backup_path: str):
        """Create a backup of the database."""
        try:
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            self.logger.info(f"Database backed up to {backup_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Backup failed: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Get table counts
            tables = ['users', 'transactions', 'budgets', 'categories']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            size = cursor.fetchone()
            stats['database_size_bytes'] = size[0] if size else 0
            
            return stats
    
    def migrate_database(self):
        """Handle database migrations for schema updates."""
        current_version = self._get_schema_version()
        
        if current_version < 1:
            self._migrate_to_v1()
        
        # Add more migrations as needed
    
    def _get_schema_version(self) -> int:
        """Get current database schema version."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )''')
                
                cursor.execute('SELECT version FROM schema_version ORDER BY version DESC LIMIT 1')
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.Error:
            return 0
    
    def _migrate_to_v1(self):
        """Migration to version 1 - adds updated_at columns if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Add updated_at columns if they don't exist
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE transactions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE budgets ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Set schema version
            cursor.execute('INSERT OR REPLACE INTO schema_version (version) VALUES (1)')
            conn.commit()

# Global database manager instance
db = DatabaseManager()