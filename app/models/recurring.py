from app import db
from datetime import datetime

class RecurringExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, yearly
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    last_created = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    split_type = db.Column(db.String(20), default='equal')
    
    # Foreign Keys
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'))
    
    # Relationships
    creator = db.relationship('User', backref='recurring_expenses')
    group = db.relationship('Group', backref='recurring_expenses')
    category = db.relationship('ExpenseCategory', backref='recurring_expenses')
    split_details = db.relationship('RecurringSplitDetail', backref='recurring_expense', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RecurringExpense {self.description} - {self.frequency}>'

class RecurringSplitDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recurring_expense_id = db.Column(db.Integer, db.ForeignKey('recurring_expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_type = db.Column(db.String(20), default='percentage')  # percentage, fixed
    share_value = db.Column(db.Float, nullable=False)  # percentage or fixed amount
    
    user = db.relationship('User', backref='recurring_splits')
    
    def __repr__(self):
        return f'<RecurringSplitDetail {self.recurring_expense_id} - User:{self.user_id}>'
