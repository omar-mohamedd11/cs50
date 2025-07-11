# Database Enhancement Guide

## Overview

This Personal Finance Tracker has been enhanced with a robust SQLite database implementation featuring advanced functionality, better organization, and comprehensive management tools.

## Enhanced Database Features

### 🔧 Database Manager (`database.py`)

The project now includes a dedicated `DatabaseManager` class that provides:

- **Connection Management**: Context managers for safe database connections
- **Error Handling**: Comprehensive error handling with logging
- **Query Utilities**: Helper methods for common database operations
- **Performance**: Optimized with indexes and connection pooling
- **Migrations**: Schema versioning and migration support
- **Backup & Restore**: Built-in backup functionality

### 📊 Enhanced Schema

#### Core Tables
1. **Users** - User authentication and profiles
2. **Transactions** - Income and expense tracking
3. **Budgets** - Monthly budget management
4. **Categories** - Organized transaction categories (NEW)
5. **User Preferences** - User-specific settings (NEW)
6. **Schema Version** - Migration tracking (NEW)

#### Key Improvements
- **Foreign Key Constraints**: Proper relationships with CASCADE delete
- **Check Constraints**: Data validation at database level
- **Indexes**: Performance optimization for common queries
- **Updated Timestamps**: Automatic tracking of record modifications

### 🎯 New Features

#### Category Management
- Pre-populated income/expense categories with colors
- Custom category creation through web interface
- Category-based transaction filtering and reporting

#### Database Statistics
- Real-time database metrics
- Storage usage monitoring
- Performance statistics
- Table record counts

#### Backup & Migration
- Automated backup creation
- Schema migration system
- Database integrity checking
- Command-line database utilities

## Using the Enhanced Database

### Web Interface

#### Categories Management
Navigate to **Categories** in the main menu to:
- View all income and expense categories
- Add custom categories with colors and descriptions
- Organize transactions by category type

#### Database Statistics
Navigate to **Stats** in the main menu to:
- View database usage statistics
- Monitor storage and performance
- Access backup functionality
- Check database health

### Command Line Tools

The `db_utils.py` script provides command-line database management:

```bash
# Initialize database with all tables and default data
python db_utils.py init

# Create a backup
python db_utils.py backup
python db_utils.py backup --backup-path /path/to/backup.db

# Run migrations
python db_utils.py migrate

# Show database statistics
python db_utils.py stats

# Check database integrity
python db_utils.py check

# Reset database (WARNING: Deletes all data!)
python db_utils.py reset
```

### Database Manager API

For developers extending the application:

```python
from database import db

# Execute queries safely
results = db.execute_query("SELECT * FROM transactions WHERE user_id = ?", (user_id,))

# Insert with automatic ID return
new_id = db.execute_insert("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type))

# Update/delete with row count
rows_affected = db.execute_update("DELETE FROM transactions WHERE id = ?", (transaction_id,))

# Get single result
user = db.execute_single("SELECT * FROM users WHERE username = ?", (username,))

# Connection context manager
with db.get_connection() as conn:
    cursor = conn.cursor()
    # Your database operations here
```

## Database Schema Details

### Indexes for Performance

```sql
-- User-related indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Transaction indexes for fast queries
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);

-- Budget indexes
CREATE INDEX idx_budgets_user_id ON budgets(user_id);
CREATE INDEX idx_budgets_month_year ON budgets(month, year);
```

### Constraints and Validation

- **Amount Validation**: All monetary amounts must be positive
- **Date Validation**: Proper date format enforcement
- **Type Validation**: Transaction types limited to 'income' or 'expense'
- **Foreign Keys**: Automatic cleanup when users are deleted
- **Unique Constraints**: Prevent duplicate usernames, emails, and budget entries

### Default Categories

The system comes pre-populated with comprehensive categories:

**Income Categories:**
- Salary, Freelance, Investment, Business, Other Income

**Expense Categories:**
- Food & Dining, Transportation, Shopping, Entertainment
- Bills & Utilities, Healthcare, Education, Travel
- Housing, Insurance, Gifts & Donations, Personal Care

Each category includes:
- Descriptive name and description
- Category type (income/expense/both)
- Color coding for visual organization
- Creation timestamps

## Migration System

The database includes a migration system for schema updates:

1. **Version Tracking**: Current schema version stored in database
2. **Automatic Migrations**: Run on application startup
3. **Safe Updates**: Non-destructive schema modifications
4. **Rollback Support**: Version-aware migration handling

## Backup and Recovery

### Automatic Backups
- Available through web interface
- Timestamped backup files
- Stored in `backups/` directory

### Manual Backups
```bash
# Create backup with timestamp
python db_utils.py backup

# Create backup with specific name
python db_utils.py backup --backup-path my_backup.db
```

### Restore Process
To restore from backup:
1. Stop the application
2. Replace `finance.db` with your backup file
3. Restart the application
4. Run migrations if needed: `python db_utils.py migrate`

## Performance Considerations

### Query Optimization
- Use indexes for all frequent query patterns
- Prepared statements prevent SQL injection
- Connection pooling reduces overhead
- Row factory enables column access by name

### Storage Management
- Regular cleanup of old transactions (if needed)
- Backup rotation to manage disk space
- Monitor database size through stats interface

### Monitoring
- Database statistics available in web interface
- Command-line tools for health checking
- Performance metrics tracking

## Security Features

- **SQL Injection Protection**: Parameterized queries throughout
- **Connection Management**: Automatic cleanup prevents leaks
- **Error Handling**: Secure error messages without data exposure
- **Transaction Safety**: Automatic rollback on errors
- **User Data Isolation**: Foreign key constraints ensure data ownership

## Troubleshooting

### Common Issues

1. **Database Locked Error**
   - Ensure no other applications are using the database
   - Check for incomplete transactions

2. **Missing Tables**
   - Run: `python db_utils.py init`
   - Check: `python db_utils.py check`

3. **Migration Errors**
   - Backup database first
   - Run: `python db_utils.py migrate`
   - If issues persist, check logs

4. **Performance Issues**
   - Monitor database size in stats
   - Consider archiving old transactions
   - Check index usage with EXPLAIN QUERY PLAN

### Database Recovery

If database corruption occurs:
1. Stop the application
2. Create backup of corrupted database
3. Restore from latest good backup
4. Re-run recent transactions if needed

## Development Guidelines

### Adding New Tables
1. Update `database.py` in `init_database()` method
2. Add appropriate indexes
3. Create migration in `migrate_database()`
4. Update schema version
5. Test migration path

### Query Best Practices
- Always use parameterized queries
- Use appropriate indexes for WHERE clauses
- Batch INSERT operations when possible
- Use transactions for multi-statement operations

### Error Handling
- Always use try/catch with database operations
- Log errors appropriately
- Provide user-friendly error messages
- Implement proper rollback on failures

This enhanced database system provides a solid foundation for the Personal Finance Tracker with room for future expansion and excellent performance characteristics.