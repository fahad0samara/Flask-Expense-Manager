from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from ..models import Expense, ExpenseCategory, Group
from .. import db

statistics = Blueprint('statistics', __name__)

@statistics.route('/statistics')
@login_required
def view_statistics():
    # Get expense statistics for the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Total expenses by category
    category_expenses = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.amount).label('total_amount')
    ).join(Expense)\
     .filter(Expense.date >= thirty_days_ago)\
     .filter(Expense.group_id.in_(
         db.session.query(Group.id)
         .join(Group.members)
         .filter_by(user_id=current_user.id)
     ))\
     .group_by(ExpenseCategory.name)\
     .all()

    # Daily expenses for the last 30 days
    daily_expenses = db.session.query(
        func.date(Expense.date).label('date'),
        func.sum(Expense.amount).label('total_amount')
    ).filter(Expense.date >= thirty_days_ago)\
     .filter(Expense.group_id.in_(
         db.session.query(Group.id)
         .join(Group.members)
         .filter_by(user_id=current_user.id)
     ))\
     .group_by(func.date(Expense.date))\
     .order_by(func.date(Expense.date))\
     .all()

    # Top spending groups
    top_groups = db.session.query(
        Group.name,
        func.sum(Expense.amount).label('total_amount')
    ).join(Expense)\
     .join(Group.members)\
     .filter(Expense.date >= thirty_days_ago)\
     .filter_by(user_id=current_user.id)\
     .group_by(Group.name)\
     .order_by(func.sum(Expense.amount).desc())\
     .limit(5)\
     .all()

    # Personal spending ratio
    total_group_expenses = db.session.query(
        func.sum(Expense.amount)
    ).filter(Expense.date >= thirty_days_ago)\
     .filter(Expense.group_id.in_(
         db.session.query(Group.id)
         .join(Group.members)
         .filter_by(user_id=current_user.id)
     ))\
     .scalar() or 0

    personal_expenses = db.session.query(
        func.sum(Expense.amount)
    ).filter(Expense.date >= thirty_days_ago)\
     .filter(Expense.payer_id == current_user.id)\
     .scalar() or 0

    return render_template('statistics/dashboard.html',
                         category_expenses=category_expenses,
                         daily_expenses=daily_expenses,
                         top_groups=top_groups,
                         total_expenses=total_group_expenses,
                         personal_expenses=personal_expenses)
