from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

app = Flask(__name__)

# In-memory storage (in production, use a proper database)
transactions = []
budgets = []
categories = [
    'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
    'Bills & Utilities', 'Healthcare', 'Travel', 'Education',
    'Groceries', 'Gas', 'Income', 'Investment', 'Other'
]

# Sample data
sample_transactions = [
    {
        'id': 1,
        'date': '2024-07-01',
        'description': 'Salary',
        'amount': 5000.00,
        'category': 'Income',
        'type': 'income'
    },
    {
        'id': 2,
        'date': '2024-07-02',
        'description': 'Grocery Store',
        'amount': -150.00,
        'category': 'Groceries',
        'type': 'expense'
    },
    {
        'id': 3,
        'date': '2024-07-03',
        'description': 'Gas Station',
        'amount': -60.00,
        'category': 'Gas',
        'type': 'expense'
    },
    {
        'id': 4,
        'date': '2024-07-05',
        'description': 'Restaurant',
        'amount': -45.00,
        'category': 'Food & Dining',
        'type': 'expense'
    },
    {
        'id': 5,
        'date': '2024-07-07',
        'description': 'Electric Bill',
        'amount': -120.00,
        'category': 'Bills & Utilities',
        'type': 'expense'
    }
]

sample_budgets = [
    {'category': 'Food & Dining', 'budget': 500, 'spent': 45},
    {'category': 'Groceries', 'budget': 400, 'spent': 150},
    {'category': 'Transportation', 'budget': 300, 'spent': 60},
    {'category': 'Entertainment', 'budget': 200, 'spent': 0},
    {'category': 'Bills & Utilities', 'budget': 500, 'spent': 120}
]

# Initialize with sample data
transactions = sample_transactions.copy()
budgets = sample_budgets.copy()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    return jsonify(transactions)

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.get_json()

    new_transaction = {
        'id': len(transactions) + 1,
        'date': data['date'],
        'description': data['description'],
        'amount': float(data['amount']),
        'category': data['category'],
        'type': 'income' if float(data['amount']) > 0 else 'expense'
    }

    transactions.append(new_transaction)
    return jsonify(new_transaction), 201

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    global transactions
    transactions = [t for t in transactions if t['id'] != transaction_id]
    return jsonify({'success': True})

@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    return jsonify(budgets)

@app.route('/api/budgets', methods=['POST'])
def add_budget():
    data = request.get_json()

    # Check if budget already exists for this category
    for budget in budgets:
        if budget['category'] == data['category']:
            budget['budget'] = float(data['budget'])
            return jsonify(budget)

    new_budget = {
        'category': data['category'],
        'budget': float(data['budget']),
        'spent': 0
    }

    budgets.append(new_budget)
    return jsonify(new_budget), 201

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    # Calculate analytics
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expenses = abs(sum(t['amount'] for t in transactions if t['type'] == 'expense'))
    net_income = total_income - total_expenses

    # Category breakdown
    category_expenses = defaultdict(float)
    for t in transactions:
        if t['type'] == 'expense':
            category_expenses[t['category']] += abs(t['amount'])

    # Monthly trends (last 6 months)
    monthly_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
    for t in transactions:
        month = t['date'][:7]  # YYYY-MM
        if t['type'] == 'income':
            monthly_data[month]['income'] += t['amount']
        else:
            monthly_data[month]['expenses'] += abs(t['amount'])

    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'category_expenses': dict(category_expenses),
        'monthly_data': dict(monthly_data)
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(categories)

if __name__ == '__main__':
    app.run(debug=True)
