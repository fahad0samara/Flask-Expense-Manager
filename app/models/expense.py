from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    
    # Relationships
    payer = relationship('User', back_populates='expenses')
    group = relationship('Group', back_populates='expenses')
    splits = relationship('ExpenseSplit', back_populates='expense')
    
    def __repr__(self):
        return f'<Expense {self.description} - ${self.amount}>'

class ExpenseSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    # Relationships
    expense = relationship('Expense', back_populates='splits')
    user = relationship('User')
    
    def __repr__(self):
        return f'<ExpenseSplit Expense:{self.expense_id} User:{self.user_id} Amount:${self.amount}>'
