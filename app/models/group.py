from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = relationship('GroupMembership', back_populates='group')
    expenses = relationship('Expense', back_populates='group')
    settlements = relationship('Settlement', back_populates='group')
    
    def __repr__(self):
        return f'<Group {self.name}>'

class GroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='group_memberships')
    group = relationship('Group', back_populates='members')
    
    def __repr__(self):
        return f'<GroupMembership User:{self.user_id} Group:{self.group_id}>'
