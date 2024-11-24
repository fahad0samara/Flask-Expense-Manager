from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.group import Group
from app.models.expense import Expense

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('main/index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    # Get user's groups
    groups = Group.query.join(Group.members).filter_by(user_id=current_user.id).all()
    
    # Get recent expenses
    recent_expenses = Expense.query.filter(
        Expense.splits.any(user_id=current_user.id)
    ).order_by(Expense.date.desc()).limit(10).all()
    
    return render_template('main/dashboard.html', 
                           user=current_user, 
                           groups=groups, 
                           recent_expenses=recent_expenses)
