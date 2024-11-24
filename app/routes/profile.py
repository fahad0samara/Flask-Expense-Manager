from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from werkzeug.utils import secure_filename
import os
from datetime import datetime

profile = Blueprint('profile', __name__)

@profile.route('/profile')
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

@profile.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Update basic information
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.currency = request.form.get('currency')
        current_user.timezone = request.form.get('timezone')
        
        # Update notification preferences
        current_user.email_notifications = request.form.get('email_notifications') == 'on'
        current_user.expense_reminders = request.form.get('expense_reminders') == 'on'
        current_user.settlement_notifications = request.form.get('settlement_notifications') == 'on'
        
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                # Create avatars directory if it doesn't exist
                avatar_dir = os.path.join('app/static/avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir)
                
                # Delete old avatar if it exists
                if current_user.avatar:
                    old_avatar_path = os.path.join(avatar_dir, current_user.avatar)
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)
                
                # Save new avatar
                filename = secure_filename(file.filename)
                file.save(os.path.join(avatar_dir, filename))
                current_user.avatar = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile'))
    
    return render_template('profile/edit_profile.html', user=current_user)

@profile.route('/profile/summary')
@login_required
def spending_summary():
    # Get spending by category for current month
    spending_by_category = current_user.get_spending_by_category(
        datetime.now().year,
        datetime.now().month
    )
    
    # Get monthly spending trend
    monthly_trend = current_user.get_monthly_spending_trend()
    
    # Get top spending groups
    top_groups = current_user.get_top_spending_groups()
    
    return render_template('profile/spending_summary.html',
                         spending_by_category=spending_by_category,
                         monthly_trend=monthly_trend,
                         top_groups=top_groups)
