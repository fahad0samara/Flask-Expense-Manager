from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

bp = Blueprint('reports', __name__)

@bp.route('/reports')
@login_required
def reports_dashboard():
    return render_template('reports/dashboard.html')

@bp.route('/reports/monthly-trend')
@login_required
def monthly_trend():
    # Get expenses for the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    monthly_expenses = (
        Expense.query
        .filter(
            Expense.created_at.between(start_date, end_date),
            Expense.splits.any(user_id=current_user.id)
        )
        .with_entities(
            func.strftime('%Y-%m', Expense.created_at).label('month'),
            func.sum(Expense.amount).label('total')
        )
        .group_by('month')
        .order_by('month')
        .all()
    )
    
    return jsonify([{
        'month': expense.month,
        'total': float(expense.total)
    } for expense in monthly_expenses])

@bp.route('/reports/category-analysis')
@login_required
def category_analysis():
    # Get category-wise spending for current month
    start_date = datetime.now().replace(day=1)
    end_date = datetime.now()
    
    category_expenses = (
        Expense.query
        .join(ExpenseCategory)
        .filter(
            Expense.created_at.between(start_date, end_date),
            Expense.splits.any(user_id=current_user.id)
        )
        .with_entities(
            ExpenseCategory.name,
            func.sum(Expense.amount).label('total')
        )
        .group_by(ExpenseCategory.name)
        .all()
    )
    
    return jsonify([{
        'category': expense.name,
        'total': float(expense.total)
    } for expense in category_expenses])

@bp.route('/reports/top-spenders')
@login_required
def top_spenders():
    # Get top spenders in user's groups
    start_date = datetime.now().replace(day=1)
    end_date = datetime.now()
    
    top_spenders = (
        User.query
        .join(User.expense_splits)
        .join(Expense)
        .filter(
            Expense.created_at.between(start_date, end_date),
            Expense.group_id.in_([group.id for group in current_user.groups])
        )
        .with_entities(
            User.username,
            func.sum(Expense.amount).label('total')
        )
        .group_by(User.id)
        .order_by(func.sum(Expense.amount).desc())
        .limit(5)
        .all()
    )
    
    return jsonify([{
        'username': spender.username,
        'total': float(spender.total)
    } for spender in top_spenders])

@bp.route('/reports/expense-forecast')
@login_required
def expense_forecast():
    # Calculate average daily spending
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    daily_avg = (
        Expense.query
        .filter(
            Expense.created_at.between(start_date, end_date),
            Expense.splits.any(user_id=current_user.id)
        )
        .with_entities(func.avg(Expense.amount).label('avg_amount'))
        .scalar() or 0
    )
    
    # Project for next month
    days_in_month = calendar.monthrange(end_date.year, end_date.month)[1]
    forecast = daily_avg * days_in_month
    
    return jsonify({
        'daily_average': float(daily_avg),
        'monthly_forecast': float(forecast)
    })
