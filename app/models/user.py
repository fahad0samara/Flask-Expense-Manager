from app import db, login_manager, bcrypt
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime

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
    
    # Relationships
    expenses = relationship('Expense', back_populates='payer')
    group_memberships = relationship('GroupMembership', back_populates='user')
    settlements_paid = relationship('Settlement', foreign_keys='Settlement.payer_id', back_populates='payer')
    settlements_received = relationship('Settlement', foreign_keys='Settlement.receiver_id', back_populates='receiver')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_total_balance(self):
        # Calculate total amount owed to others
        owed_to_others = db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).filter_by(user_id=self.id).scalar() or 0
        
        # Calculate total amount others owe to user
        owed_by_others = db.session.query(
            db.func.sum(Expense.amount)
        ).filter_by(payer_id=self.id).scalar() or 0
        
        return owed_by_others - owed_to_others
    
    def get_monthly_spending(self, year, month):
        return db.session.query(
            db.func.sum(ExpenseSplit.amount)
        ).join(Expense).filter(
            ExpenseSplit.user_id == self.id,
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == month
        ).scalar() or 0
    
    def __repr__(self):
        return f'<User {self.username}>'
