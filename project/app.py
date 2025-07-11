from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Database initialization
def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
        category TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        description TEXT,
        date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Budgets table
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, category, month, year)
    )''')
    
    conn.commit()
    conn.close()

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
            conn = sqlite3.connect('finance.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                     (username, email, password_hash))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
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
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # Get current month's data
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    # Total income and expenses for current month
    c.execute('''SELECT 
        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses
        FROM transactions 
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?''',
        (session['user_id'], f'{current_month:02d}', str(current_year)))
    
    totals = c.fetchone()
    total_income = totals[0] or 0
    total_expenses = totals[1] or 0
    
    # Recent transactions
    c.execute('''SELECT type, category, amount, description, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC, created_at DESC 
                LIMIT 5''', (session['user_id'],))
    recent_transactions = c.fetchall()
    
    # Category-wise expenses for current month
    c.execute('''SELECT category, SUM(amount) 
                FROM transactions 
                WHERE user_id = ? AND type = 'expense' 
                AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
                GROUP BY category 
                ORDER BY SUM(amount) DESC''',
                (session['user_id'], f'{current_month:02d}', str(current_year)))
    expense_categories = c.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=total_income - total_expenses,
                         recent_transactions=recent_transactions,
                         expense_categories=expense_categories)

@app.route('/transactions')
@login_required
def transactions():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute('''SELECT id, type, category, amount, description, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC, created_at DESC''', (session['user_id'],))
    all_transactions = c.fetchall()
    conn.close()
    
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
        
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        c.execute('''INSERT INTO transactions (user_id, type, category, amount, description, date)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], transaction_type, category, amount, description, date))
        conn.commit()
        conn.close()
        
        flash('Transaction added successfully!')
        return redirect(url_for('transactions'))
    
    return render_template('add_transaction.html')

@app.route('/budgets')
@login_required
def budgets():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    # Get budgets for current month
    c.execute('''SELECT category, amount FROM budgets 
                WHERE user_id = ? AND month = ? AND year = ?''',
                (session['user_id'], current_month, current_year))
    user_budgets = c.fetchall()
    
    # Get actual spending for each budget category
    budget_data = []
    for category, budget_amount in user_budgets:
        c.execute('''SELECT COALESCE(SUM(amount), 0) FROM transactions 
                    WHERE user_id = ? AND type = 'expense' AND category = ?
                    AND strftime('%m', date) = ? AND strftime('%Y', date) = ?''',
                    (session['user_id'], category, f'{current_month:02d}', str(current_year)))
        spent = c.fetchone()[0]
        budget_data.append({
            'category': category,
            'budget': budget_amount,
            'spent': spent,
            'remaining': budget_amount - spent
        })
    
    conn.close()
    return render_template('budgets.html', budgets=budget_data)

@app.route('/add_budget', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        month = int(request.form['month'])
        year = int(request.form['year'])
        
        conn = sqlite3.connect('finance.db')
        c = conn.cursor()
        try:
            c.execute('''INSERT OR REPLACE INTO budgets (user_id, category, amount, month, year)
                        VALUES (?, ?, ?, ?, ?)''',
                     (session['user_id'], category, amount, month, year))
            conn.commit()
            flash('Budget set successfully!')
        except Exception as e:
            flash('Error setting budget!')
        finally:
            conn.close()
        
        return redirect(url_for('budgets'))
    
    return render_template('add_budget.html')

@app.route('/api/chart-data')
@login_required
def chart_data():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # Get last 6 months of income and expenses
    data = []
    for i in range(6):
        date = datetime.datetime.now() - datetime.timedelta(days=i*30)
        month = date.month
        year = date.year
        
        c.execute('''SELECT 
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
            FROM transactions 
            WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?''',
            (session['user_id'], f'{month:02d}', str(year)))
        
        result = c.fetchone()
        data.append({
            'month': date.strftime('%b %Y'),
            'income': result[0] or 0,
            'expenses': result[1] or 0
        })
    
    conn.close()
    return jsonify(data[::-1])  # Reverse to show oldest first

if __name__ == '__main__':
    init_db()
    app.run(debug=True)