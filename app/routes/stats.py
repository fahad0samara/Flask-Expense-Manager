from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.models import ExpenseCategory, Group
import json

bp = Blueprint('stats', __name__)

@bp.route('/stats')
@login_required
def view_stats():
    # Get date range
    end_date = datetime.now()
    start_date = end_date - relativedelta(months=6)
    
    # Get spending by category
    category_spending = current_user.get_spending_by_category(start_date, end_date)
    
    # Format data for charts
    category_labels = [item[0] for item in category_spending]
    category_values = [float(item[1]) for item in category_spending]
    
    # Get monthly spending trend
    months = []
    spending_trend = []
    current = start_date
    while current <= end_date:
        amount = current_user.get_monthly_spending(current.year, current.month)
        months.append(current.strftime('%B %Y'))
        spending_trend.append(float(amount))
        current += relativedelta(months=1)
    
    # Get recent activity
    recent_activity = current_user.get_recent_activity(limit=10)
    
    return render_template('stats/view_stats.html',
                         category_labels=json.dumps(category_labels),
                         category_values=json.dumps(category_values),
                         months=json.dumps(months),
                         spending_trend=json.dumps(spending_trend),
                         recent_activity=recent_activity)
