from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7))  # Hex color code
    
    # Relationships
    expenses = relationship('Expense', back_populates='category')
    
    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    split_type = db.Column(db.String(20), default='equal')  # equal, percentage, custom
    currency = db.Column(db.String(3), default='USD')
    receipt_image = db.Column(db.String(200))
    notes = db.Column(db.Text)
    
    # Foreign Keys
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'))
    
    # Relationships
    payer = relationship('User', back_populates='expenses')
    group = relationship('Group', back_populates='expenses')
    category = relationship('ExpenseCategory', back_populates='expenses')
    splits = relationship('ExpenseSplit', back_populates='expense', cascade='all, delete-orphan')
    
    def calculate_splits(self, split_data=None):
        """Calculate expense splits based on split type"""
        if self.split_type == 'equal':
            total_members = len(self.group.members) if self.group else 1
            split_amount = self.amount / total_members
            return [(member.user_id, split_amount) for member in self.group.members]
        
        elif self.split_type == 'percentage':
            return [(user_id, (percentage/100) * self.amount) 
                   for user_id, percentage in split_data.items()]
        
        elif self.split_type == 'custom':
            return [(user_id, amount) for user_id, amount in split_data.items()]
        
        return []
    
    def __repr__(self):
        return f'<Expense {self.description} - ${self.amount}>'

class ExpenseSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float)  # For percentage-based splits
    
    # Relationships
    expense = relationship('Expense', back_populates='splits')
    user = relationship('User')
    
    def __repr__(self):
        return f'<ExpenseSplit Expense:{self.expense_id} User:{self.user_id} Amount:${self.amount}>'
