# from flask_mail import Message  # Temporarily commented out
from .. import db  # Temporarily removed mail import
from ..models.user import User
from ..models.notification import Notification
from datetime import datetime
import json

class NotificationService:
    def __init__(self):
        self.notification_types = {
            'spending_alert': self._handle_spending_alert,
            'anomaly_alert': self._handle_anomaly_alert,
            'budget_alert': self._handle_budget_alert,
            'trend_alert': self._handle_trend_alert
        }
        
    def set_alert(self, user_id, alert_type, threshold, notification_method='app'):  # Changed default to 'app'
        """Set up a new alert for a user"""
        if alert_type not in self.notification_types:
            raise ValueError(f"Invalid alert type: {alert_type}")
            
        notification = Notification(
            user_id=user_id,
            type=alert_type,
            settings=json.dumps({
                'threshold': threshold,
                'method': notification_method
            }),
            created_at=datetime.now(),
            is_active=True
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification.id
        
    def send_notification(self, user_id, alert_type, data):
        """Send a notification based on alert type and user preferences"""
        user = User.query.get(user_id)
        if not user:
            return False
            
        if alert_type in self.notification_types:
            return self.notification_types[alert_type](user, data)
            
        return False
        
    def _handle_spending_alert(self, user, data):
        """Handle spending threshold alerts"""
        subject = "Spending Alert - Threshold Exceeded"
        body = f"""
        Hi {user.name},
        
        Your spending in {data['category']} has exceeded your set threshold.
        
        Current spending: ${data['current_amount']:.2f}
        Threshold: ${data['threshold']:.2f}
        Excess: ${data['excess']:.2f}
        
        View details: {data['details_url']}
        
        Best regards,
        Your Splitwise Team
        """
        
        return self._send_notification(user, subject, body)
        
    def _handle_anomaly_alert(self, user, data):
        """Handle anomaly detection alerts"""
        subject = "Unusual Spending Pattern Detected"
        body = f"""
        Hi {user.name},
        
        We've detected an unusual spending pattern in your recent transactions.
        
        Transaction Details:
        - Amount: ${data['amount']:.2f}
        - Category: {data['category']}
        - Date: {data['date']}
        - Confidence Score: {data['confidence_score']:.2f}
        
        This transaction appears to be {data['deviation_percent']}% different from your usual spending pattern in this category.
        
        View details: {data['details_url']}
        
        Best regards,
        Your Splitwise Team
        """
        
        return self._send_notification(user, subject, body)
        
    def _handle_budget_alert(self, user, data):
        """Handle budget-related alerts"""
        subject = "Budget Alert - Category Limit Approaching"
        body = f"""
        Hi {user.name},
        
        You're approaching your budget limit in {data['category']}.
        
        Current Status:
        - Spent: ${data['spent']:.2f}
        - Budget: ${data['budget']:.2f}
        - Remaining: ${data['remaining']:.2f}
        - Percentage Used: {data['percentage_used']}%
        
        Recommendations:
        {data['recommendations']}
        
        View details: {data['details_url']}
        
        Best regards,
        Your Splitwise Team
        """
        
        return self._send_notification(user, subject, body)
        
    def _handle_trend_alert(self, user, data):
        """Handle trend-based alerts"""
        subject = "Spending Trend Alert"
        body = f"""
        Hi {user.name},
        
        We've noticed a significant trend in your spending pattern.
        
        Trend Details:
        - Category: {data['category']}
        - Time Period: {data['period']}
        - Change: {data['change_percent']}%
        - Average Change: ${data['average_change']:.2f}
        
        Analysis:
        {data['analysis']}
        
        Recommendations:
        {data['recommendations']}
        
        View details: {data['details_url']}
        
        Best regards,
        Your Splitwise Team
        """
        
        return self._send_notification(user, subject, body)
        
    def _send_notification(self, user, subject, body):
        """Send notification"""
        notification = Notification(
            user_id=user.id,
            type='app_notification',
            title=subject,
            message=body,
            created_at=datetime.now(),
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return True
