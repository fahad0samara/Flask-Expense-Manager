from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from werkzeug.utils import secure_filename
import os

bp = Blueprint('profile', __name__)

@bp.route('/profile')
@login_required
def view_profile():
    monthly_spending = current_user.get_monthly_spending(
        datetime.now().year,
        datetime.now().month
    )
    total_balance = current_user.get_total_balance()
    
    return render_template('profile/view_profile.html',
                         user=current_user,
                         monthly_spending=monthly_spending,
                         total_balance=total_balance)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.currency = request.form.get('currency')
        current_user.timezone = request.form.get('timezone')
        
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join('app/static/avatars', filename))
                current_user.avatar = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile'))
    
    return render_template('profile/edit_profile.html', user=current_user)

@bp.route('/profile/summary')
@login_required
def spending_summary():
    # Get spending by category for current month
    spending_by_category = db.session.query(
        ExpenseCategory.name,
        db.func.sum(ExpenseSplit.amount)
    ).join(Expense).join(ExpenseSplit).filter(
        ExpenseSplit.user_id == current_user.id
    ).group_by(ExpenseCategory.name).all()
    
    # Get monthly totals for the year
    monthly_totals = []
    for month in range(1, 13):
        total = current_user.get_monthly_spending(
            datetime.now().year,
            month
        )
        monthly_totals.append(total)
    
    return render_template('profile/spending_summary.html',
                         spending_by_category=spending_by_category,
                         monthly_totals=monthly_totals)
