from app import db
from datetime import datetime

class Settlement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    notes = db.Column(db.Text)
    
    # Foreign Keys
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    
    # Relationships
    payer = db.relationship('User', foreign_keys=[payer_id], back_populates='settlements_paid')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='settlements_received')
    group = db.relationship('Group', back_populates='settlements')
    
    def __repr__(self):
        return f'<Settlement ${self.amount} from {self.payer.username} to {self.receiver.username}>'
