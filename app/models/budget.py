from app import db
from datetime import datetime

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # monthly, yearly
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'))
    
    # Relationships
    user = db.relationship('User', backref='budgets')
    group = db.relationship('Group', backref='budgets')
    category = db.relationship('ExpenseCategory', backref='budgets')
    
    def get_current_spending(self):
        """Calculate current spending for this budget period"""
        from app.models.expense import Expense, ExpenseSplit
        
        query = db.session.query(db.func.sum(ExpenseSplit.amount))
        query = query.join(Expense)
        
        # Apply filters based on budget type
        if self.group_id:
            query = query.filter(Expense.group_id == self.group_id)
        if self.category_id:
            query = query.filter(Expense.category_id == self.category_id)
        if not self.group_id:  # Personal budget
            query = query.filter(ExpenseSplit.user_id == self.user_id)
            
        # Apply date filter
        query = query.filter(Expense.date >= self.start_date)
        if self.end_date:
            query = query.filter(Expense.date <= self.end_date)
            
        return query.scalar() or 0.0
    
    def get_remaining_amount(self):
        """Calculate remaining budget amount"""
        current_spending = self.get_current_spending()
        return self.amount - current_spending
    
    def get_percentage_used(self):
        """Calculate percentage of budget used"""
        if self.amount == 0:
            return 100.0
        return (self.get_current_spending() / self.amount) * 100
    
    def __repr__(self):
        return f'<Budget {self.name} - {self.amount}>'

class BudgetAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    threshold_percentage = db.Column(db.Float, nullable=False)  # e.g., 80 for 80%
    is_triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)
    
    budget = db.relationship('Budget', backref='alerts')
    
    def __repr__(self):
        return f'<BudgetAlert Budget:{self.budget_id} - {self.threshold_percentage}%>'
