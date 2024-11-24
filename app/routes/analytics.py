from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense, ExpenseCategory, ExpenseSplit
from app.models.group import Group
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar

analytics = Blueprint('analytics', __name__)

@analytics.route('/analytics')
@login_required
def dashboard():
    # Get total spending by category for current month
    current_month = datetime.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    category_spending = db.session.query(
        ExpenseCategory.name,
        func.sum(ExpenseSplit.amount).label('total')
    ).join(
        Expense, ExpenseCategory.id == Expense.category_id
    ).join(
        ExpenseSplit
    ).filter(
        ExpenseSplit.user_id == current_user.id,
        Expense.date >= current_month,
        Expense.date < next_month
    ).group_by(
        ExpenseCategory.name
    ).all()
    
    # Get monthly spending trend
    months = []
    spending_trend = []
    for i in range(12):
        date = (datetime.now() - timedelta(days=30*i)).replace(day=1)
        total = db.session.query(
            func.sum(ExpenseSplit.amount)
        ).join(Expense).filter(
            ExpenseSplit.user_id == current_user.id,
            Expense.date >= date,
            Expense.date < (date + timedelta(days=32)).replace(day=1)
        ).scalar() or 0
        
        months.insert(0, date.strftime('%B %Y'))
        spending_trend.insert(0, float(total))
    
    # Get group spending distribution
    group_spending = db.session.query(
        Group.name,
        func.sum(ExpenseSplit.amount).label('total')
    ).join(
        Expense, Group.id == Expense.group_id
    ).join(
        ExpenseSplit
    ).filter(
        ExpenseSplit.user_id == current_user.id,
        Expense.date >= current_month,
        Expense.date < next_month
    ).group_by(
        Group.name
    ).all()
    
    return render_template('analytics/dashboard.html',
                         category_spending=category_spending,
                         months=months,
                         spending_trend=spending_trend,
                         group_spending=group_spending)

@analytics.route('/analytics/expense-patterns')
@login_required
def expense_patterns():
    # Get spending by day of week
    daily_pattern = db.session.query(
        func.strftime('%w', Expense.date).label('day'),
        func.avg(ExpenseSplit.amount).label('avg_amount')
    ).join(ExpenseSplit).filter(
        ExpenseSplit.user_id == current_user.id
    ).group_by('day').all()
    
    # Get spending by time of day
    hourly_pattern = db.session.query(
        func.strftime('%H', Expense.date).label('hour'),
        func.avg(ExpenseSplit.amount).label('avg_amount')
    ).join(ExpenseSplit).filter(
        ExpenseSplit.user_id == current_user.id
    ).group_by('hour').all()
    
    # Get recurring expense patterns
    recurring_patterns = db.session.query(
        Expense.description,
        func.count(Expense.id).label('frequency'),
        func.avg(Expense.amount).label('avg_amount')
    ).join(ExpenseSplit).filter(
        ExpenseSplit.user_id == current_user.id
    ).group_by(
        Expense.description
    ).having(
        func.count(Expense.id) > 1
    ).order_by(
        func.count(Expense.id).desc()
    ).limit(10).all()
    
    return render_template('analytics/expense_patterns.html',
                         daily_pattern=daily_pattern,
                         hourly_pattern=hourly_pattern,
                         recurring_patterns=recurring_patterns)

@analytics.route('/analytics/group-insights/<int:group_id>')
@login_required
def group_insights(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Ensure user is member of the group
    if group.id not in [g.id for g in current_user.groups]:
        flash('You do not have permission to view this group\'s insights.', 'error')
        return redirect(url_for('analytics.dashboard'))
    
    # Get member contribution distribution
    member_contributions = db.session.query(
        User.username,
        func.sum(Expense.amount).label('total_paid')
    ).join(
        Expense, User.id == Expense.payer_id
    ).filter(
        Expense.group_id == group_id
    ).group_by(
        User.username
    ).all()
    
    # Get category distribution for group
    category_distribution = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.amount).label('total')
    ).join(
        Expense, ExpenseCategory.id == Expense.category_id
    ).filter(
        Expense.group_id == group_id
    ).group_by(
        ExpenseCategory.name
    ).all()
    
    # Get monthly spending trend for group
    months = []
    group_trend = []
    for i in range(6):
        date = (datetime.now() - timedelta(days=30*i)).replace(day=1)
        total = db.session.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.group_id == group_id,
            Expense.date >= date,
            Expense.date < (date + timedelta(days=32)).replace(day=1)
        ).scalar() or 0
        
        months.insert(0, date.strftime('%B %Y'))
        group_trend.insert(0, float(total))
    
    return render_template('analytics/group_insights.html',
                         group=group,
                         member_contributions=member_contributions,
                         category_distribution=category_distribution,
                         months=months,
                         group_trend=group_trend)

@analytics.route('/api/analytics/spending-trend')
@login_required
def api_spending_trend():
    """API endpoint for getting spending trend data"""
    months = []
    spending = []
    for i in range(12):
        date = (datetime.now() - timedelta(days=30*i)).replace(day=1)
        total = db.session.query(
            func.sum(ExpenseSplit.amount)
        ).join(Expense).filter(
            ExpenseSplit.user_id == current_user.id,
            Expense.date >= date,
            Expense.date < (date + timedelta(days=32)).replace(day=1)
        ).scalar() or 0
        
        months.insert(0, date.strftime('%B %Y'))
        spending.insert(0, float(total))
    
    return jsonify({
        'labels': months,
        'data': spending
    })
