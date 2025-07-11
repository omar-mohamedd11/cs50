#!/usr/bin/env python3
"""
Database utilities for the Personal Finance Tracker.
Command-line tools for database management operations.
"""

import argparse
import os
import sys
import datetime
from database import db

def init_database():
    """Initialize the database with all tables and default data."""
    print("Initializing database...")
    try:
        db.init_database()
        print("✓ Database initialized successfully!")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    return True

def backup_database(backup_path=None):
    """Create a database backup."""
    if not backup_path:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"finance_backup_{timestamp}.db"
    
    print(f"Creating backup: {backup_path}")
    try:
        # Create backups directory if it doesn't exist
        backup_dir = os.path.dirname(backup_path) or 'backups'
        if backup_dir != '.' and not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        if not backup_path.startswith('/') and backup_dir != '.':
            backup_path = os.path.join(backup_dir, os.path.basename(backup_path))
            
        db.backup_database(backup_path)
        print(f"✓ Backup created successfully: {backup_path}")
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False
    return True

def migrate_database():
    """Run database migrations."""
    print("Running database migrations...")
    try:
        db.migrate_database()
        print("✓ Database migrations completed successfully!")
    except Exception as e:
        print(f"✗ Database migration failed: {e}")
        return False
    return True

def show_stats():
    """Display database statistics."""
    print("Database Statistics:")
    print("=" * 50)
    try:
        stats = db.get_database_stats()
        
        print(f"Users:        {stats.get('users_count', 0)}")
        print(f"Transactions: {stats.get('transactions_count', 0)}")
        print(f"Budgets:      {stats.get('budgets_count', 0)}")
        print(f"Categories:   {stats.get('categories_count', 0)}")
        
        size_bytes = stats.get('database_size_bytes', 0)
        if size_bytes > 0:
            size_kb = size_bytes / 1024
            if size_kb < 1024:
                print(f"DB Size:      {size_kb:.2f} KB")
            else:
                print(f"DB Size:      {size_kb/1024:.2f} MB")
        else:
            print("DB Size:      N/A")
            
        print("=" * 50)
    except Exception as e:
        print(f"✗ Failed to retrieve statistics: {e}")
        return False
    return True

def check_database():
    """Check database integrity and connectivity."""
    print("Checking database...")
    try:
        # Test basic connectivity
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("✓ Database connectivity: OK")
            else:
                print("✗ Database connectivity: FAILED")
                return False
        
        # Check if all required tables exist
        tables = ['users', 'transactions', 'budgets', 'categories', 'user_preferences']
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in tables if table not in existing_tables]
            if missing_tables:
                print(f"✗ Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                print("✓ All required tables exist")
        
        print("✓ Database check completed successfully!")
    except Exception as e:
        print(f"✗ Database check failed: {e}")
        return False
    return True

def reset_database():
    """Reset database (WARNING: This will delete all data!)."""
    print("⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Type 'YES' to confirm database reset: ")
    
    if confirm != 'YES':
        print("Database reset cancelled.")
        return False
    
    try:
        # Remove existing database file
        if os.path.exists(db.db_path):
            os.remove(db.db_path)
            print("✓ Existing database file removed")
        
        # Reinitialize database
        db.init_database()
        print("✓ Database reset and reinitialized successfully!")
    except Exception as e:
        print(f"✗ Database reset failed: {e}")
        return False
    return True

def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(description='Database utilities for Personal Finance Tracker')
    parser.add_argument('command', choices=[
        'init', 'backup', 'migrate', 'stats', 'check', 'reset'
    ], help='Command to execute')
    parser.add_argument('--backup-path', type=str, help='Path for database backup')
    
    args = parser.parse_args()
    
    # Execute the requested command
    success = True
    
    if args.command == 'init':
        success = init_database()
    elif args.command == 'backup':
        success = backup_database(args.backup_path)
    elif args.command == 'migrate':
        success = migrate_database()
    elif args.command == 'stats':
        success = show_stats()
    elif args.command == 'check':
        success = check_database()
    elif args.command == 'reset':
        success = reset_database()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()