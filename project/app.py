from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from functools import wraps
import os
from database import db

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if not username or not email or not password:
            flash('All fields are required!')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        
        try:
            user_id = db.execute_insert(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            
            # Create default user preferences
            db.execute_insert(
                'INSERT INTO user_preferences (user_id) VALUES (?)',
                (user_id,)
            )
            
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                flash('Username or email already exists!')
            else:
                flash('Registration failed. Please try again.')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.execute_single(
            'SELECT id, password_hash FROM users WHERE username = ?', 
            (username,)
        )
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get current month's data
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    # Total income and expenses for current month
    totals = db.execute_single('''SELECT 
        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses
        FROM transactions 
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?''',
        (session['user_id'], f'{current_month:02d}', str(current_year)))
    
    total_income = totals['total_income'] or 0
    total_expenses = totals['total_expenses'] or 0
    
    # Recent transactions
    recent_transactions = db.execute_query('''SELECT type, category, amount, description, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC, created_at DESC 
                LIMIT 5''', (session['user_id'],))
    
    # Category-wise expenses for current month
    expense_categories = db.execute_query('''SELECT category, SUM(amount) as total
                FROM transactions 
                WHERE user_id = ? AND type = 'expense' 
                AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
                GROUP BY category 
                ORDER BY SUM(amount) DESC''',
                (session['user_id'], f'{current_month:02d}', str(current_year)))
    
    return render_template('dashboard.html', 
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=total_income - total_expenses,
                         recent_transactions=recent_transactions,
                         expense_categories=expense_categories)

@app.route('/transactions')
@login_required
def transactions():
    all_transactions = db.execute_query('''SELECT id, type, category, amount, description, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC, created_at DESC''', (session['user_id'],))
    
    return render_template('transactions.html', transactions=all_transactions)

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        transaction_type = request.form['type']
        category = request.form['category']
        amount = float(request.form['amount'])
        description = request.form['description']
        date = request.form['date']
        
        db.execute_insert('''INSERT INTO transactions (user_id, type, category, amount, description, date)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], transaction_type, category, amount, description, date))
        
        flash('Transaction added successfully!')
        return redirect(url_for('transactions'))
    
    # Get categories from database
    income_categories = db.execute_query(
        "SELECT name FROM categories WHERE type IN ('income', 'both') ORDER BY name"
    )
    expense_categories = db.execute_query(
        "SELECT name FROM categories WHERE type IN ('expense', 'both') ORDER BY name"
    )
    
    return render_template('add_transaction.html', 
                         income_categories=income_categories,
                         expense_categories=expense_categories)

@app.route('/budgets')
@login_required
def budgets():
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    # Get budgets for current month
    user_budgets = db.execute_query('''SELECT category, amount FROM budgets 
                WHERE user_id = ? AND month = ? AND year = ?''',
                (session['user_id'], current_month, current_year))
    
    # Get actual spending for each budget category
    budget_data = []
    for budget in user_budgets:
        spent_result = db.execute_single('''SELECT COALESCE(SUM(amount), 0) as spent FROM transactions 
                    WHERE user_id = ? AND type = 'expense' AND category = ?
                    AND strftime('%m', date) = ? AND strftime('%Y', date) = ?''',
                    (session['user_id'], budget['category'], f'{current_month:02d}', str(current_year)))
        
        spent = spent_result['spent']
        budget_data.append({
            'category': budget['category'],
            'budget': budget['amount'],
            'spent': spent,
            'remaining': budget['amount'] - spent
        })
    
    return render_template('budgets.html', budgets=budget_data)

@app.route('/add_budget', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        month = int(request.form['month'])
        year = int(request.form['year'])
        
        try:
            db.execute_update('''INSERT OR REPLACE INTO budgets (user_id, category, amount, month, year)
                        VALUES (?, ?, ?, ?, ?)''',
                     (session['user_id'], category, amount, month, year))
            flash('Budget set successfully!')
        except Exception as e:
            flash('Error setting budget!')
        
        return redirect(url_for('budgets'))
    
    # Get expense categories for budget creation
    expense_categories = db.execute_query(
        "SELECT name FROM categories WHERE type IN ('expense', 'both') ORDER BY name"
    )
    
    return render_template('add_budget.html', expense_categories=expense_categories)

@app.route('/api/chart-data')
@login_required
def chart_data():
    # Get last 6 months of income and expenses
    data = []
    for i in range(6):
        date = datetime.datetime.now() - datetime.timedelta(days=i*30)
        month = date.month
        year = date.year
        
        result = db.execute_single('''SELECT 
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
            FROM transactions 
            WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?''',
            (session['user_id'], f'{month:02d}', str(year)))
        
        data.append({
            'month': date.strftime('%b %Y'),
            'income': result['income'] or 0,
            'expenses': result['expenses'] or 0
        })
    
    return jsonify(data[::-1])  # Reverse to show oldest first

@app.route('/categories')
@login_required
def categories():
    """View and manage transaction categories."""
    all_categories = db.execute_query(
        'SELECT * FROM categories ORDER BY type, name'
    )
    return render_template('categories.html', categories=all_categories)

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    """Add a new transaction category."""
    name = request.form['name']
    category_type = request.form['type']
    description = request.form.get('description', '')
    color = request.form.get('color', '#6366f1')
    
    try:
        db.execute_insert(
            'INSERT INTO categories (name, type, description, color) VALUES (?, ?, ?, ?)',
            (name, category_type, description, color)
        )
        flash('Category added successfully!')
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            flash('Category name already exists!')
        else:
            flash('Error adding category!')
    
    return redirect(url_for('categories'))

@app.route('/delete_transaction/<int:transaction_id>')
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction."""
    rows_affected = db.execute_update(
        'DELETE FROM transactions WHERE id = ? AND user_id = ?',
        (transaction_id, session['user_id'])
    )
    
    if rows_affected > 0:
        flash('Transaction deleted successfully!')
    else:
        flash('Transaction not found or access denied!')
    
    return redirect(url_for('transactions'))

@app.route('/backup')
@login_required
def backup():
    """Create a database backup (admin functionality)."""
    try:
        backup_filename = f"finance_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join('backups', backup_filename)
        
        # Create backups directory if it doesn't exist
        os.makedirs('backups', exist_ok=True)
        
        db.backup_database(backup_path)
        flash(f'Database backed up successfully to {backup_filename}!')
    except Exception as e:
        flash(f'Backup failed: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/stats')
@login_required
def stats():
    """View database statistics."""
    stats = db.get_database_stats()
    return render_template('stats.html', stats=stats)

if __name__ == '__main__':
    # Initialize database with all tables and default data
    db.init_database()
    
    # Run migrations if needed
    db.migrate_database()
    
    app.run(debug=True)