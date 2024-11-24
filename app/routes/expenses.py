from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense, ExpenseSplit
from app.models.group import Group

expenses = Blueprint('expenses', __name__)

@expenses.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    # Get user's groups for dropdown
    groups = Group.query.join(Group.members).filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        group_id = request.form.get('group_id')
        split_type = request.form.get('split_type')
        
        # Create expense
        expense = Expense(
            description=description, 
            amount=amount, 
            payer_id=current_user.id,
            group_id=group_id if group_id else None
        )
        db.session.add(expense)
        
        # Handle expense splits
        if split_type == 'equal':
            # Get group members if group selected, otherwise just current user
            if group_id:
                group = Group.query.get(group_id)
                members = [membership.user for membership in group.members]
            else:
                members = [current_user]
            
            split_amount = amount / len(members)
            
            for member in members:
                if member.id != current_user.id:
                    split = ExpenseSplit(
                        expense=expense, 
                        user_id=member.id, 
                        amount=split_amount
                    )
                    db.session.add(split)
        
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('expenses/add_expense.html', groups=groups)

@expenses.route('/expense/<int:expense_id>/details')
@login_required
def expense_details(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Ensure user has access to this expense
    if not any(split.user_id == current_user.id for split in expense.splits):
        flash('You do not have access to this expense.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('expenses/expense_details.html', expense=expense)
