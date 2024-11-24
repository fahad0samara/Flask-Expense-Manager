from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Expense, ExpenseSplit, ExpenseCategory, User, Group
from datetime import datetime

bp = Blueprint('expense', __name__)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        title = request.form.get('title')
        amount = float(request.form.get('amount'))
        category_id = request.form.get('category')
        group_id = request.form.get('group')
        split_type = request.form.get('split_type', 'equal')
        description = request.form.get('description', '')
        
        expense = Expense(
            title=title,
            amount=amount,
            description=description,
            created_by=current_user.id,
            category_id=category_id,
            group_id=group_id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        # Handle expense splits based on split_type
        if split_type == 'equal':
            group = Group.query.get(group_id)
            members = group.members
            split_amount = amount / len(members)
            
            for member in members:
                split = ExpenseSplit(
                    expense_id=expense.id,
                    user_id=member.id,
                    amount=split_amount
                )
                db.session.add(split)
        
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expense.view_expenses'))
    
    categories = ExpenseCategory.query.all()
    groups = Group.query.filter(Group.members.any(id=current_user.id)).all()
    return render_template('expense/add.html', categories=categories, groups=groups)

@bp.route('/', methods=['GET'])
@login_required
def view_expenses():
    expenses = Expense.query.filter(
        (Expense.created_by == current_user.id) |
        (Expense.splits.any(ExpenseSplit.user_id == current_user.id))
    ).order_by(Expense.date.desc()).all()
    return render_template('expense/list.html', expenses=expenses)

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
