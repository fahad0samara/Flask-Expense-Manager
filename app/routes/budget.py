from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.budget import Budget, BudgetAlert
from app.models.expense import Expense, ExpenseCategory
from app.models.notification import Notification
from datetime import datetime, timedelta
import calendar

bp = Blueprint('budget', __name__)

@bp.route('/budgets')
@login_required
def list_budgets():
    personal_budgets = Budget.query.filter_by(
        user_id=current_user.id,
        group_id=None
    ).order_by(Budget.created_at.desc()).all()
    
    group_budgets = Budget.query.filter(
        Budget.group_id.in_([g.id for g in current_user.groups])
    ).order_by(Budget.created_at.desc()).all()
    
    return render_template('budget/list_budgets.html',
                         personal_budgets=personal_budgets,
                         group_budgets=group_budgets)

@bp.route('/budgets/new', methods=['GET', 'POST'])
@login_required
def create_budget():
    if request.method == 'POST':
        name = request.form.get('name')
        amount = float(request.form.get('amount'))
        period = request.form.get('period')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = request.form.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        group_id = request.form.get('group_id')
        category_id = request.form.get('category_id')
        
        budget = Budget(
            name=name,
            amount=amount,
            period=period,
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id,
            group_id=group_id,
            category_id=category_id
        )
        
        db.session.add(budget)
        
        # Create budget alerts
        for threshold in [50, 80, 100]:
            alert = BudgetAlert(
                budget=budget,
                threshold_percentage=threshold
            )
            db.session.add(alert)
        
        db.session.commit()
        flash('Budget created successfully!', 'success')
        return redirect(url_for('budget.list_budgets'))
    
    categories = ExpenseCategory.query.all()
    groups = current_user.groups
    return render_template('budget/create_budget.html',
                         categories=categories,
                         groups=groups)

@bp.route('/budgets/<int:budget_id>')
@login_required
def view_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    
    # Check if user has permission to view
    if budget.user_id != current_user.id and (
        not budget.group_id or
        budget.group_id not in [g.id for g in current_user.groups]
    ):
        flash('You do not have permission to view this budget.', 'error')
        return redirect(url_for('budget.list_budgets'))
    
    # Get spending data for charts
    spending_data = []
    if budget.period == 'monthly':
        days_in_month = calendar.monthrange(
            budget.start_date.year,
            budget.start_date.month
        )[1]
        for day in range(1, days_in_month + 1):
            date = budget.start_date.replace(day=day)
            if budget.end_date and date > budget.end_date:
                break
            
            daily_spending = db.session.query(
                db.func.sum(Expense.amount)
            ).filter(
                Expense.date >= date,
                Expense.date < date + timedelta(days=1)
            )
            
            if budget.category_id:
                daily_spending = daily_spending.filter(
                    Expense.category_id == budget.category_id
                )
            if budget.group_id:
                daily_spending = daily_spending.filter(
                    Expense.group_id == budget.group_id
                )
            else:
                daily_spending = daily_spending.join(ExpenseSplit).filter(
                    ExpenseSplit.user_id == current_user.id
                )
            
            spending_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'amount': daily_spending.scalar() or 0
            })
    
    return render_template('budget/view_budget.html',
                         budget=budget,
                         spending_data=spending_data)

@bp.route('/budgets/<int:budget_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    
    # Check if user has permission to edit
    if budget.user_id != current_user.id:
        flash('You do not have permission to edit this budget.', 'error')
        return redirect(url_for('budget.list_budgets'))
    
    if request.method == 'POST':
        budget.name = request.form.get('name')
        budget.amount = float(request.form.get('amount'))
        budget.period = request.form.get('period')
        budget.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        
        end_date = request.form.get('end_date')
        budget.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        
        budget.group_id = request.form.get('group_id')
        budget.category_id = request.form.get('category_id')
        
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budget.view_budget', budget_id=budget.id))
    
    categories = ExpenseCategory.query.all()
    groups = current_user.groups
    return render_template('budget/edit_budget.html',
                         budget=budget,
                         categories=categories,
                         groups=groups)

def check_budget_alerts():
    """
    Function to be run by scheduler to check budget thresholds and create notifications
    """
    active_budgets = Budget.query.filter_by(is_active=True).all()
    
    for budget in active_budgets:
        percentage_used = budget.get_percentage_used()
        
        for alert in budget.alerts:
            if not alert.is_triggered and percentage_used >= alert.threshold_percentage:
                # Create notification
                notification = Notification(
                    user_id=budget.user_id,
                    title=f'Budget Alert: {budget.name}',
                    message=f'Your budget "{budget.name}" has reached {alert.threshold_percentage}% of its limit.',
                    type='budget',
                    budget_id=budget.id
                )
                db.session.add(notification)
                
                # Mark alert as triggered
                alert.is_triggered = True
                alert.triggered_at = datetime.utcnow()
                
                db.session.commit()
