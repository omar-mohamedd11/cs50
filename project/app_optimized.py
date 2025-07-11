from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_caching import Cache
from flask_cors import CORS
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv
import logging
from functools import wraps

# Import our models and validators
from models import db, Transaction, Budget, Category
from validators import validate_transaction_data, validate_budget_data, validate_category_data

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///budget_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'simple')
app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))

# Initialize extensions
db.init_app(app)
cache = Cache(app)
CORS(app)

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function

# Cache invalidation decorator
def invalidate_cache_on_change(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        # Invalidate relevant cache keys
        cache.delete('analytics_data')
        cache.delete('all_budgets')
        cache.delete('all_transactions')
        return result
    return decorated_function

@app.before_first_request
def create_tables():
    """Create database tables and populate initial data"""
    db.create_all()
    
    # Initialize categories if they don't exist
    if Category.query.count() == 0:
        default_categories = [
            'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
            'Bills & Utilities', 'Healthcare', 'Travel', 'Education',
            'Groceries', 'Gas', 'Income', 'Investment', 'Other'
        ]
        
        for cat_name in default_categories:
            category = Category(name=cat_name)
            db.session.add(category)
        
        db.session.commit()
        logger.info("Default categories created")
    
    # Add sample data if no transactions exist
    if Transaction.query.count() == 0:
        sample_transactions = [
            Transaction(
                date=date(2024, 7, 1),
                description='Salary',
                amount=5000.00,
                category='Income',
                type='income'
            ),
            Transaction(
                date=date(2024, 7, 2),
                description='Grocery Store',
                amount=-150.00,
                category='Groceries',
                type='expense'
            ),
            Transaction(
                date=date(2024, 7, 3),
                description='Gas Station',
                amount=-60.00,
                category='Gas',
                type='expense'
            ),
            Transaction(
                date=date(2024, 7, 5),
                description='Restaurant',
                amount=-45.00,
                category='Food & Dining',
                type='expense'
            ),
            Transaction(
                date=date(2024, 7, 7),
                description='Electric Bill',
                amount=-120.00,
                category='Bills & Utilities',
                type='expense'
            )
        ]
        
        for transaction in sample_transactions:
            db.session.add(transaction)
        
        # Add sample budgets
        sample_budgets = [
            Budget(category='Food & Dining', budget=500),
            Budget(category='Groceries', budget=400),
            Budget(category='Transportation', budget=300),
            Budget(category='Entertainment', budget=200),
            Budget(category='Bills & Utilities', budget=500)
        ]
        
        for budget in sample_budgets:
            db.session.add(budget)
        
        db.session.commit()
        logger.info("Sample data created")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transactions', methods=['GET'])
@handle_errors
def get_transactions():
    """Get all transactions with optional filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = Transaction.query
    
    if category:
        query = query.filter(Transaction.category == category)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Order by date (newest first) and paginate
    query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
    
    if request.args.get('no_pagination'):
        transactions = query.all()
        return jsonify([t.to_dict() for t in transactions])
    
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@app.route('/api/transactions', methods=['POST'])
@handle_errors
@invalidate_cache_on_change
def add_transaction():
    """Add a new transaction with validation"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate input data
    validated_data, errors = validate_transaction_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Determine transaction type
    transaction_type = 'income' if validated_data['amount'] > 0 else 'expense'
    
    # Create new transaction
    transaction = Transaction(
        date=validated_data['date'],
        description=validated_data['description'],
        amount=validated_data['amount'],
        category=validated_data['category'],
        type=transaction_type
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    logger.info(f"Transaction added: {transaction.description} - {transaction.amount}")
    return jsonify(transaction.to_dict()), 201

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@handle_errors
@invalidate_cache_on_change
def update_transaction(transaction_id):
    """Update an existing transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate input data
    validated_data, errors = validate_transaction_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Update transaction
    transaction.date = validated_data['date']
    transaction.description = validated_data['description']
    transaction.amount = validated_data['amount']
    transaction.category = validated_data['category']
    transaction.type = 'income' if validated_data['amount'] > 0 else 'expense'
    transaction.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    logger.info(f"Transaction updated: {transaction.id}")
    return jsonify(transaction.to_dict())

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@handle_errors
@invalidate_cache_on_change
def delete_transaction(transaction_id):
    """Delete a transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    db.session.delete(transaction)
    db.session.commit()
    
    logger.info(f"Transaction deleted: {transaction_id}")
    return jsonify({'success': True})

@app.route('/api/budgets', methods=['GET'])
@handle_errors
def get_budgets():
    """Get all budgets with current spending"""
    cached_budgets = cache.get('all_budgets')
    if cached_budgets:
        return jsonify(cached_budgets)
    
    budgets = Budget.query.all()
    budget_data = [budget.to_dict() for budget in budgets]
    
    cache.set('all_budgets', budget_data, timeout=300)
    return jsonify(budget_data)

@app.route('/api/budgets', methods=['POST'])
@handle_errors
@invalidate_cache_on_change
def add_budget():
    """Add or update a budget"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate input data
    validated_data, errors = validate_budget_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Check if budget already exists for this category
    budget = Budget.query.filter_by(category=validated_data['category']).first()
    
    if budget:
        # Update existing budget
        budget.budget = validated_data['budget']
        budget.updated_at = datetime.utcnow()
        status_code = 200
        logger.info(f"Budget updated: {budget.category}")
    else:
        # Create new budget
        budget = Budget(
            category=validated_data['category'],
            budget=validated_data['budget']
        )
        db.session.add(budget)
        status_code = 201
        logger.info(f"Budget created: {budget.category}")
    
    db.session.commit()
    return jsonify(budget.to_dict()), status_code

@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@handle_errors
@invalidate_cache_on_change
def delete_budget(budget_id):
    """Delete a budget"""
    budget = Budget.query.get_or_404(budget_id)
    
    db.session.delete(budget)
    db.session.commit()
    
    logger.info(f"Budget deleted: {budget_id}")
    return jsonify({'success': True})

@app.route('/api/analytics', methods=['GET'])
@handle_errors
def get_analytics():
    """Get analytics data with caching"""
    # Try to get from cache first
    cached_analytics = cache.get('analytics_data')
    if cached_analytics:
        return jsonify(cached_analytics)
    
    # Calculate analytics using optimized database queries
    analytics = Transaction.get_analytics()
    
    # Cache the result
    cache.set('analytics_data', analytics, timeout=300)
    
    return jsonify(analytics)

@app.route('/api/categories', methods=['GET'])
@handle_errors
def get_categories():
    """Get all categories"""
    categories = Category.query.order_by(Category.name).all()
    return jsonify([category.name for category in categories])

@app.route('/api/categories', methods=['POST'])
@handle_errors
def add_category():
    """Add a new category"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate input data
    validated_data, errors = validate_category_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Check if category already exists
    existing_category = Category.query.filter_by(name=validated_data['name']).first()
    if existing_category:
        return jsonify({'error': 'Category already exists'}), 409
    
    # Create new category
    category = Category(name=validated_data['name'])
    db.session.add(category)
    db.session.commit()
    
    logger.info(f"Category created: {category.name}")
    return jsonify(category.to_dict()), 201

@app.route('/api/dashboard', methods=['GET'])
@handle_errors
def get_dashboard_data():
    """Get combined dashboard data in a single API call"""
    # Get recent transactions (last 5)
    recent_transactions = Transaction.query.order_by(
        Transaction.date.desc(), Transaction.id.desc()
    ).limit(5).all()
    
    # Get analytics (cached)
    analytics = get_analytics().get_json()
    
    # Get budgets (cached)
    budgets = get_budgets().get_json()
    
    # Get categories
    categories = get_categories().get_json()
    
    return jsonify({
        'recent_transactions': [t.to_dict() for t in recent_transactions],
        'analytics': analytics,
        'budgets': budgets,
        'categories': categories
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Add response headers for caching and compression
@app.after_request
def after_request(response):
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Add caching headers for static files
    if request.endpoint == 'static':
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    
    return response

if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )