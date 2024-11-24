from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.recurring import RecurringExpense, RecurringSplitDetail
from app.models.expense import Expense, ExpenseSplit
from app.models.group import Group
from app.models.user import User
from datetime import datetime, timedelta

recurring = Blueprint('recurring', __name__)

@recurring.route('/recurring')
@login_required
def list_recurring():
    recurring_expenses = RecurringExpense.query.filter(
        (RecurringExpense.creator_id == current_user.id) |
        (RecurringExpense.group_id.in_([g.id for g in current_user.groups]))
    ).order_by(RecurringExpense.start_date.desc()).all()
    
    return render_template('recurring/list_recurring.html',
                         recurring_expenses=recurring_expenses)

@recurring.route('/recurring/new', methods=['GET', 'POST'])
@login_required
def create_recurring():
    if request.method == 'POST':
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        frequency = request.form.get('frequency')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = request.form.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        group_id = request.form.get('group_id')
        category_id = request.form.get('category_id')
        split_type = request.form.get('split_type', 'equal')
        
        recurring_expense = RecurringExpense(
            description=description,
            amount=amount,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            creator_id=current_user.id,
            group_id=group_id,
            category_id=category_id,
            split_type=split_type
        )
        
        db.session.add(recurring_expense)
        
        # Handle split details
        if split_type != 'equal':
            split_data = request.form.getlist('split_users[]')
            split_values = request.form.getlist('split_values[]')
            split_types = request.form.getlist('split_types[]')
            
            for user_id, value, type in zip(split_data, split_values, split_types):
                split_detail = RecurringSplitDetail(
                    recurring_expense=recurring_expense,
                    user_id=int(user_id),
                    share_type=type,
                    share_value=float(value)
                )
                db.session.add(split_detail)
        
        db.session.commit()
        flash('Recurring expense created successfully!', 'success')
        return redirect(url_for('recurring.list_recurring'))
    
    groups = Group.query.join(Group.members).filter_by(user_id=current_user.id).all()
    return render_template('recurring/create_recurring.html', groups=groups)

@recurring.route('/recurring/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recurring(expense_id):
    recurring_expense = RecurringExpense.query.get_or_404(expense_id)
    
    # Check if user has permission to edit
    if recurring_expense.creator_id != current_user.id:
        flash('You do not have permission to edit this recurring expense.', 'error')
        return redirect(url_for('recurring.list_recurring'))
    
    if request.method == 'POST':
        recurring_expense.description = request.form.get('description')
        recurring_expense.amount = float(request.form.get('amount'))
        recurring_expense.frequency = request.form.get('frequency')
        recurring_expense.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        
        end_date = request.form.get('end_date')
        recurring_expense.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        
        recurring_expense.group_id = request.form.get('group_id')
        recurring_expense.category_id = request.form.get('category_id')
        recurring_expense.split_type = request.form.get('split_type', 'equal')
        
        # Update split details
        if recurring_expense.split_type != 'equal':
            # Remove old split details
            RecurringSplitDetail.query.filter_by(recurring_expense_id=expense_id).delete()
            
            # Add new split details
            split_data = request.form.getlist('split_users[]')
            split_values = request.form.getlist('split_values[]')
            split_types = request.form.getlist('split_types[]')
            
            for user_id, value, type in zip(split_data, split_values, split_types):
                split_detail = RecurringSplitDetail(
                    recurring_expense=recurring_expense,
                    user_id=int(user_id),
                    share_type=type,
                    share_value=float(value)
                )
                db.session.add(split_detail)
        
        db.session.commit()
        flash('Recurring expense updated successfully!', 'success')
        return redirect(url_for('recurring.list_recurring'))
    
    groups = Group.query.join(Group.members).filter_by(user_id=current_user.id).all()
    return render_template('recurring/edit_recurring.html',
                         expense=recurring_expense,
                         groups=groups)

@recurring.route('/recurring/<int:expense_id>/toggle', methods=['POST'])
@login_required
def toggle_recurring(expense_id):
    recurring_expense = RecurringExpense.query.get_or_404(expense_id)
    
    if recurring_expense.creator_id != current_user.id:
        flash('You do not have permission to modify this recurring expense.', 'error')
        return redirect(url_for('recurring.list_recurring'))
    
    recurring_expense.is_active = not recurring_expense.is_active
    db.session.commit()
    
    status = 'activated' if recurring_expense.is_active else 'deactivated'
    flash(f'Recurring expense {status} successfully!', 'success')
    return redirect(url_for('recurring.list_recurring'))

def create_recurring_expenses():
    """
    Function to be run by scheduler to create expenses from recurring templates
    """
    now = datetime.utcnow()
    active_recurring = RecurringExpense.query.filter_by(is_active=True).all()
    
    for recurring in active_recurring:
        if recurring.end_date and recurring.end_date < now:
            continue
            
        last_created = recurring.last_created or recurring.start_date
        should_create = False
        
        if recurring.frequency == 'daily':
            should_create = (now - last_created).days >= 1
        elif recurring.frequency == 'weekly':
            should_create = (now - last_created).days >= 7
        elif recurring.frequency == 'monthly':
            # Check if it's been a month since last creation
            next_date = last_created.replace(day=1) + timedelta(days=32)
            next_date = next_date.replace(day=1)
            should_create = now >= next_date
        elif recurring.frequency == 'yearly':
            # Check if it's been a year since last creation
            should_create = (
                now.year > last_created.year or
                (now.year == last_created.year and now.month > last_created.month)
            )
        
        if should_create:
            # Create new expense from template
            expense = Expense(
                description=recurring.description,
                amount=recurring.amount,
                payer_id=recurring.creator_id,
                group_id=recurring.group_id,
                category_id=recurring.category_id,
                split_type=recurring.split_type
            )
            db.session.add(expense)
            
            # Create expense splits
            if recurring.split_type == 'equal':
                total_members = len(recurring.group.members) if recurring.group else 1
                split_amount = recurring.amount / total_members
                
                for member in (recurring.group.members if recurring.group else [recurring.creator]):
                    split = ExpenseSplit(
                        expense=expense,
                        user_id=member.user_id if hasattr(member, 'user_id') else member.id,
                        amount=split_amount
                    )
                    db.session.add(split)
            else:
                for split_detail in recurring.split_details:
                    amount = (
                        split_detail.share_value
                        if split_detail.share_type == 'fixed'
                        else (split_detail.share_value / 100) * recurring.amount
                    )
                    split = ExpenseSplit(
                        expense=expense,
                        user_id=split_detail.user_id,
                        amount=amount
                    )
                    db.session.add(split)
            
            recurring.last_created = now
            db.session.commit()
