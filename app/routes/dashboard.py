from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import db, Expense, ExpenseCategory, Group, ExpenseSplit
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    # Get total expenses for current user
    total_expenses = db.session.query(func.sum(ExpenseSplit.amount))\
        .filter(ExpenseSplit.user_id == current_user.id)\
        .scalar() or 0

    # Get expenses by category
    category_expenses = db.session.query(
        ExpenseCategory.name,
        func.sum(ExpenseSplit.amount).label('total')
    ).join(Expense, Expense.category_id == ExpenseCategory.id)\
     .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)\
     .filter(ExpenseSplit.user_id == current_user.id)\
     .group_by(ExpenseCategory.name)\
     .all()

    # Get monthly expenses for the last 6 months
    today = datetime.today()
    six_months_ago = today - timedelta(days=180)
    monthly_expenses = db.session.query(
        func.strftime('%Y-%m', Expense.date).label('month'),
        func.sum(ExpenseSplit.amount).label('total')
    ).join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)\
     .filter(ExpenseSplit.user_id == current_user.id)\
     .filter(Expense.date >= six_months_ago)\
     .group_by('month')\
     .order_by('month')\
     .all()

    # Get top groups by expense
    top_groups = db.session.query(
        Group.name,
        func.sum(ExpenseSplit.amount).label('total')
    ).join(Expense, Expense.group_id == Group.id)\
     .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)\
     .filter(ExpenseSplit.user_id == current_user.id)\
     .group_by(Group.name)\
     .order_by(func.sum(ExpenseSplit.amount).desc())\
     .limit(5)\
     .all()

    # Calculate amount owed and amount to receive
    amount_owed = db.session.query(func.sum(ExpenseSplit.amount))\
        .join(Expense)\
        .filter(ExpenseSplit.user_id == current_user.id)\
        .filter(Expense.payer_id != current_user.id)\
        .scalar() or 0

    amount_to_receive = db.session.query(func.sum(ExpenseSplit.amount))\
        .join(Expense)\
        .filter(ExpenseSplit.user_id != current_user.id)\
        .filter(Expense.payer_id == current_user.id)\
        .scalar() or 0

    # Format monthly expenses for chart
    months = []
    amounts = []
    for month, amount in monthly_expenses:
        year, month = month.split('-')
        month_name = calendar.month_abbr[int(month)]
        months.append(f"{month_name} {year}")
        amounts.append(float(amount))

    # Format category expenses for chart
    categories = []
    category_amounts = []
    for category, amount in category_expenses:
        categories.append(category)
        category_amounts.append(float(amount))

    return render_template('dashboard/index.html',
                         total_expenses=total_expenses,
                         amount_owed=amount_owed,
                         amount_to_receive=amount_to_receive,
                         months=months,
                         amounts=amounts,
                         categories=categories,
                         category_amounts=category_amounts,
                         top_groups=top_groups)
