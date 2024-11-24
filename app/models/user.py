from app import db, login_manager, bcrypt
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.expense import ExpenseSplit, Expense, ExpenseCategory
from app.models.settlement import Settlement
from dateutil.relativedelta import relativedelta

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Additional profile fields
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    currency = db.Column(db.String(3), default='USD')
    timezone = db.Column(db.String(50), default='UTC')
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    expense_reminders = db.Column(db.Boolean, default=True)
    settlement_notifications = db.Column(db.Boolean, default=True)
    
    # Activity tracking
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
    # Preferences
    default_currency = db.Column(db.String(3), default='USD')
    language = db.Column(db.String(5), default='en_US')
    date_format = db.Column(db.String(20), default='MM/DD/YYYY')
    
    # Relationships
    expenses = relationship('Expense', back_populates='payer')
    expense_splits = relationship('ExpenseSplit', back_populates='user')
    group_memberships = relationship('GroupMembership', back_populates='user')
    settlements_paid = relationship('Settlement', foreign_keys='Settlement.payer_id', back_populates='payer')
    settlements_received = relationship('Settlement', foreign_keys='Settlement.receiver_id', back_populates='receiver')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_total_balance(self):
        """Calculate total balance (positive means you'll receive money)"""
        # Money you'll receive
        to_receive = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(Expense).filter(
            Expense.payer_id == self.id,
            ExpenseSplit.user_id != self.id
        ).scalar() or 0
        
        # Money you owe
        to_pay = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(Expense).filter(
            ExpenseSplit.user_id == self.id,
            Expense.payer_id != self.id
        ).scalar() or 0
        
        return to_receive - to_pay
    
    def get_monthly_spending(self, year, month):
        """Get total spending for a specific month"""
        return db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(Expense).filter(
            ExpenseSplit.user_id == self.id,
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == month
        ).scalar() or 0
    
    def get_spending_by_category(self, start_date=None, end_date=None):
        """Get spending breakdown by category"""
        if not start_date:
            start_date = datetime.now() - relativedelta(months=1)
        if not end_date:
            end_date = datetime.now()
            
        return db.session.query(
            ExpenseCategory.name,
            db.func.sum(ExpenseSplit.amount).label('total')
        ).join(
            Expense, ExpenseSplit.expense_id == Expense.id
        ).join(
            ExpenseCategory, Expense.category_id == ExpenseCategory.id
        ).filter(
            ExpenseSplit.user_id == self.id,
            Expense.date.between(start_date, end_date)
        ).group_by(
            ExpenseCategory.name
        ).all()
    
    def get_recent_activity(self, limit=10):
        """Get recent expenses and settlements"""
        # Get recent expenses
        expenses = db.session.query(Expense).join(
            ExpenseSplit
        ).filter(
            db.or_(
                Expense.payer_id == self.id,
                ExpenseSplit.user_id == self.id
            )
        ).order_by(
            Expense.date.desc()
        ).limit(limit).all()
        
        # Get recent settlements
        settlements = db.session.query(Settlement).filter(
            db.or_(
                Settlement.payer_id == self.id,
                Settlement.receiver_id == self.id
            )
        ).order_by(
            Settlement.date.desc()
        ).limit(limit).all()
        
        # Combine and sort by date
        activities = expenses + settlements
        activities.sort(key=lambda x: x.date, reverse=True)
        return activities[:limit]
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = datetime.utcnow()
        db.session.commit()
    
    def record_login(self):
        """Record user login"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
