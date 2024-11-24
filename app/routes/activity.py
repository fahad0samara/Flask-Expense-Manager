from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime, timedelta
from ..models import Expense, Group, User, ExpenseSplit
from .. import db

activity = Blueprint('activity', __name__)

@activity.route('/activity')
@login_required
def view_activity():
    # Get all groups the user is part of
    user_groups = db.session.query(Group.id)\
        .join(Group.members)\
        .filter_by(user_id=current_user.id)\
        .all()
    group_ids = [g.id for g in user_groups]

    # Get recent expenses from user's groups
    recent_expenses = db.session.query(
        Expense,
        User.username.label('payer_name'),
        Group.name.label('group_name')
    ).join(User, User.id == Expense.payer_id)\
     .join(Group)\
     .filter(Expense.group_id.in_(group_ids))\
     .order_by(desc(Expense.date))\
     .limit(20)\
     .all()

    # Get expense details including splits
    activity_items = []
    for expense, payer_name, group_name in recent_expenses:
        splits = db.session.query(
            ExpenseSplit,
            User.username
        ).join(User, User.id == ExpenseSplit.user_id)\
         .filter(ExpenseSplit.expense_id == expense.id)\
         .all()

        activity_items.append({
            'expense': expense,
            'payer_name': payer_name,
            'group_name': group_name,
            'splits': splits
        })

    return render_template('activity/feed.html', 
                         activity_items=activity_items)

@activity.route('/api/activity/recent')
@login_required
def get_recent_activity():
    # Get activities in the last hour
    last_hour = datetime.now() - timedelta(hours=1)
    
    user_groups = db.session.query(Group.id)\
        .join(Group.members)\
        .filter_by(user_id=current_user.id)\
        .all()
    group_ids = [g.id for g in user_groups]

    recent_activities = db.session.query(
        Expense,
        User.username.label('payer_name'),
        Group.name.label('group_name')
    ).join(User, User.id == Expense.payer_id)\
     .join(Group)\
     .filter(Expense.group_id.in_(group_ids))\
     .filter(Expense.date >= last_hour)\
     .order_by(desc(Expense.date))\
     .all()

    activities = []
    for expense, payer_name, group_name in recent_activities:
        activities.append({
            'type': 'expense',
            'description': expense.description,
            'amount': float(expense.amount),
            'payer': payer_name,
            'group': group_name,
            'date': expense.date.isoformat()
        })

    return jsonify(activities)
