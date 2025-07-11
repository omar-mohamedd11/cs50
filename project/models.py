from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'amount': self.amount,
            'category': self.category,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_analytics(cls):
        """Optimized analytics calculation using database queries"""
        # Total income and expenses
        total_income = db.session.query(func.sum(cls.amount)).filter(
            cls.type == 'income'
        ).scalar() or 0
        
        total_expenses = abs(db.session.query(func.sum(cls.amount)).filter(
            cls.type == 'expense'
        ).scalar() or 0)
        
        # Category breakdown
        category_expenses = db.session.query(
            cls.category,
            func.sum(func.abs(cls.amount))
        ).filter(cls.type == 'expense').group_by(cls.category).all()
        
        # Monthly data
        monthly_data = db.session.query(
            func.strftime('%Y-%m', cls.date).label('month'),
            cls.type,
            func.sum(func.abs(cls.amount)).label('total')
        ).group_by('month', cls.type).all()
        
        # Process monthly data
        monthly_dict = {}
        for month, trans_type, total in monthly_data:
            if month not in monthly_dict:
                monthly_dict[month] = {'income': 0, 'expenses': 0}
            if trans_type == 'income':
                monthly_dict[month]['income'] = total
            else:
                monthly_dict[month]['expenses'] = total
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': total_income - total_expenses,
            'category_expenses': dict(category_expenses),
            'monthly_data': monthly_dict
        }

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False, unique=True)
    budget = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        # Calculate spent amount for this category
        spent = db.session.query(func.sum(func.abs(Transaction.amount))).filter(
            Transaction.category == self.category,
            Transaction.type == 'expense'
        ).scalar() or 0
        
        return {
            'id': self.id,
            'category': self.category,
            'budget': self.budget,
            'spent': spent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }