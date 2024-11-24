from app import db
from datetime import datetime

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # expense, settlement, budget, reminder
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional reference IDs
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'))
    settlement_id = db.Column(db.Integer, db.ForeignKey('settlement.id'))
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    expense = db.relationship('Expense', backref='notifications')
    settlement = db.relationship('Settlement', backref='notifications')
    budget = db.relationship('Budget', backref='notifications')
    group = db.relationship('Group', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.type} - {self.title}>'

class UserNotificationPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # App notification preferences
    notify_new_expense = db.Column(db.Boolean, default=True)
    notify_expense_reminder = db.Column(db.Boolean, default=True)
    notify_settlement_request = db.Column(db.Boolean, default=True)
    notify_monthly_summary = db.Column(db.Boolean, default=True)
    notify_budget_alert = db.Column(db.Boolean, default=True)
    
    # Reminder settings
    reminder_frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    reminder_day = db.Column(db.Integer)  # day of week (0-6) or day of month (1-31)
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)
    
    # Relationship
    user = db.relationship('User', backref='notification_preferences')
    
    def __repr__(self):
        return f'<UserNotificationPreference User:{self.user_id}>'
