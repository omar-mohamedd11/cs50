from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, date

class TransactionSchema(Schema):
    date = fields.Date(required=True)
    description = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    amount = fields.Float(required=True, validate=validate.Range(min=-999999.99, max=999999.99))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))

class BudgetSchema(Schema):
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    budget = fields.Float(required=True, validate=validate.Range(min=0.01, max=999999.99))

class CategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

def validate_transaction_data(data):
    """Validate transaction data and return errors if any"""
    schema = TransactionSchema()
    try:
        result = schema.load(data)
        return result, None
    except ValidationError as err:
        return None, err.messages

def validate_budget_data(data):
    """Validate budget data and return errors if any"""
    schema = BudgetSchema()
    try:
        result = schema.load(data)
        return result, None
    except ValidationError as err:
        return None, err.messages

def validate_category_data(data):
    """Validate category data and return errors if any"""
    schema = CategorySchema()
    try:
        result = schema.load(data)
        return result, None
    except ValidationError as err:
        return None, err.messages