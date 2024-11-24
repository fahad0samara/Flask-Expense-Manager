from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Expense, ExpenseSplit, ExpenseCategory, User, Group
from datetime import datetime

bp = Blueprint('expense', __name__)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    group_id = request.args.get('group_id')
    if group_id:
        group = Group.query.get_or_404(group_id)
        if not any(member.user_id == current_user.id for member in group.members):
            flash('You do not have permission to add expenses to this group.', 'error')
            return redirect(url_for('group.list_groups'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        amount = float(request.form.get('amount'))
        category_id = request.form.get('category')
        group_id = request.form.get('group')
        split_type = request.form.get('split_type', 'equal')
        description = request.form.get('description', '')
        
        # Verify group membership again
        group = Group.query.get_or_404(group_id)
        if not any(member.user_id == current_user.id for member in group.members):
            flash('You do not have permission to add expenses to this group.', 'error')
            return redirect(url_for('group.list_groups'))
        
        # Create expense
        expense = Expense(
            title=title,
            amount=amount,
            description=description,
            date=datetime.now(),
            paid_by=current_user.id,
            category_id=category_id,
            group_id=group_id
        )
        
        db.session.add(expense)
        db.session.flush()  # Get expense ID without committing
        
        # Handle expense splits based on split_type
        members = group.members
        total_split = 0
        splits = []
        
        if split_type == 'equal':
            split_amount = amount / len(members)
            for member in members:
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    user_id=member.user_id,
                    amount=split_amount
                ))
                total_split += split_amount
        
        elif split_type == 'percentage':
            for member in members:
                percentage = float(request.form.get(f'percentage_{member.user_id}', 0))
                split_amount = (percentage / 100) * amount
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    user_id=member.user_id,
                    amount=split_amount
                ))
                total_split += split_amount
        
        elif split_type == 'shares':
            total_shares = sum(int(request.form.get(f'shares_{member.user_id}', 1)) for member in members)
            for member in members:
                shares = int(request.form.get(f'shares_{member.user_id}', 1))
                split_amount = (shares / total_shares) * amount
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    user_id=member.user_id,
                    amount=split_amount
                ))
                total_split += split_amount
        
        elif split_type == 'exact':
            for member in members:
                split_amount = float(request.form.get(f'amount_{member.user_id}', 0))
                splits.append(ExpenseSplit(
                    expense_id=expense.id,
                    user_id=member.user_id,
                    amount=split_amount
                ))
                total_split += split_amount
        
        # Verify total split amount matches expense amount
        if abs(total_split - amount) > 0.01:  # Allow for small floating-point differences
            db.session.rollback()
            flash('The sum of split amounts must equal the total expense amount.', 'error')
            return redirect(url_for('expense.add_expense', group_id=group_id))
        
        # Add all splits
        for split in splits:
            db.session.add(split)
        
        try:
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('group.view_group', group_id=group_id))
        except Exception as e:
            db.session.rollback()
            flash('Error adding expense. Please try again.', 'error')
            return redirect(url_for('expense.add_expense', group_id=group_id))
    
    # GET request - show form
    categories = ExpenseCategory.query.all()
    groups = Group.query.join(Group.members).filter_by(user_id=current_user.id).all()
    
    return render_template('expense/add.html',
                         categories=categories,
                         groups=groups,
                         selected_group_id=group_id)

@bp.route('/', methods=['GET'])
@login_required
def view_expenses():
    group_id = request.args.get('group_id')
    if group_id:
        group = Group.query.get_or_404(group_id)
        if not any(member.user_id == current_user.id for member in group.members):
            flash('You do not have permission to view expenses for this group.', 'error')
            return redirect(url_for('group.list_groups'))
        expenses = Expense.query.filter_by(group_id=group_id).order_by(Expense.date.desc()).all()
    else:
        # Show expenses from all groups the user is a member of
        group_ids = [m.group_id for m in current_user.group_memberships]
        expenses = Expense.query.filter(Expense.group_id.in_(group_ids)).order_by(Expense.date.desc()).all()
    
    return render_template('expense/list.html', expenses=expenses, group_id=group_id)

@bp.route('/<int:expense_id>', methods=['GET'])
@login_required
def view_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.created_by != current_user.id and not any(split.user_id == current_user.id for split in expense.splits):
        flash('You do not have permission to view this expense.', 'error')
        return redirect(url_for('expense.view_expenses'))
    return render_template('expense/detail.html', expense=expense)

@bp.route('/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.created_by != current_user.id:
        flash('You do not have permission to edit this expense.', 'error')
        return redirect(url_for('expense.view_expenses'))
    
    if request.method == 'POST':
        expense.title = request.form.get('title')
        expense.amount = float(request.form.get('amount'))
        expense.category_id = request.form.get('category')
        expense.description = request.form.get('description', '')
        
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expense.view_expense', expense_id=expense.id))
    
    categories = ExpenseCategory.query.all()
    return render_template('expense/edit.html', expense=expense, categories=categories)

@bp.route('/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.created_by != current_user.id:
        flash('You do not have permission to delete this expense.', 'error')
        return redirect(url_for('expense.view_expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expense.view_expenses'))
