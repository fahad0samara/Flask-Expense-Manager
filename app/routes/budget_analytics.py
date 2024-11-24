from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.budget import Budget
from app.models.expense import Expense, ExpenseCategory
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

bp = Blueprint('budget_analytics', __name__)

@bp.route('/budget-analytics')
@login_required
def analytics_dashboard():
    try:
        return render_template('budget_analytics/dashboard.html')
    except Exception as e:
        print(f"Error rendering dashboard: {str(e)}")
        return str(e), 500

@bp.route('/budget-analytics/overview')
@login_required
def budget_overview():
    """Get overview of all active budgets"""
    try:
        active_budgets = Budget.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        overview_data = []
        total_budget = 0
        total_spent = 0
        
        for budget in active_budgets:
            try:
                spent = budget.get_current_spending()
                remaining = budget.get_remaining_amount()
                percentage = budget.get_percentage_used()
                
                overview_data.append({
                    'name': budget.name,
                    'total': float(budget.amount),
                    'spent': float(spent),
                    'remaining': float(remaining),
                    'percentage': float(percentage),
                    'category': budget.category.name if budget.category else 'Uncategorized',
                    'period': budget.period
                })
                
                total_budget += budget.amount
                total_spent += spent
            except Exception as e:
                print(f"Error processing budget {budget.id}: {str(e)}")
                continue
        
        return jsonify({
            'budgets': overview_data,
            'summary': {
                'total_budget': float(total_budget),
                'total_spent': float(total_spent),
                'total_remaining': float(total_budget - total_spent),
                'overall_percentage': (total_spent / total_budget * 100) if total_budget > 0 else 0
            }
        })
    except Exception as e:
        print(f"Error in budget overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/budget-analytics/savings-potential')
@login_required
def savings_potential():
    """Analyze potential savings based on spending patterns"""
    try:
        # Get all expenses from last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        expenses = Expense.query.join(Expense.splits).filter(
            Expense.created_at.between(start_date, end_date),
            Expense.splits.any(user_id=current_user.id)
        ).all()
        
        # Analyze recurring expenses
        recurring_expenses = {}
        for expense in expenses:
            key = (expense.category_id, expense.description)
            if key not in recurring_expenses:
                recurring_expenses[key] = []
            recurring_expenses[key].append(expense.amount)
        
        savings_suggestions = []
        for (cat_id, desc), amounts in recurring_expenses.items():
            if len(amounts) >= 3:  # If expense occurs at least 3 times
                avg_amount = sum(amounts) / len(amounts)
                max_amount = max(amounts)
                if max_amount > avg_amount * 1.2:  # If max is 20% above average
                    category = ExpenseCategory.query.get(cat_id)
                    savings_suggestions.append({
                        'description': desc,
                        'category': category.name if category else 'Uncategorized',
                        'average_amount': float(avg_amount),
                        'highest_amount': float(max_amount),
                        'potential_saving': float(max_amount - avg_amount),
                        'occurrence_count': len(amounts)
                    })
        
        return jsonify(savings_suggestions)
    except Exception as e:
        print(f"Error in savings potential: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/budget-analytics/category-efficiency')
@login_required
def category_efficiency():
    """Analyze budget efficiency by category"""
    try:
        categories = ExpenseCategory.query.all()
        efficiency_data = []
        
        for category in categories:
            # Get budgets for this category
            budgets = Budget.query.filter_by(
                user_id=current_user.id,
                category_id=category.id,
                is_active=True
            ).all()
            
            if budgets:
                total_budget = sum(b.amount for b in budgets)
                total_spent = sum(b.get_current_spending() for b in budgets)
                
                efficiency_data.append({
                    'category': category.name,
                    'budget_amount': float(total_budget),
                    'actual_spent': float(total_spent),
                    'efficiency_score': float((total_budget - total_spent) / total_budget * 100) if total_budget > 0 else 0,
                    'status': 'Under Budget' if total_spent <= total_budget else 'Over Budget'
                })
        
        return jsonify(efficiency_data)
    except Exception as e:
        print(f"Error in category efficiency: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/budget-analytics/forecast')
@login_required
def budget_forecast():
    """Forecast future budget requirements"""
    try:
        # Analyze last 6 months of spending
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        monthly_spending = db.session.query(
            func.strftime('%Y-%m', Expense.created_at).label('month'),
            func.sum(Expense.amount).label('total')
        ).join(Expense.splits).filter(
            Expense.created_at.between(start_date, end_date),
            Expense.splits.any(user_id=current_user.id)
        ).group_by('month').all()
        
        # Calculate trend
        if len(monthly_spending) >= 2:
            spending_trend = []
            for i in range(len(monthly_spending) - 1):
                current_month = float(monthly_spending[i].total or 0)
                next_month = float(monthly_spending[i + 1].total or 0)
                if current_month > 0:
                    change = ((next_month - current_month) / current_month) * 100
                    spending_trend.append(change)
            
            if spending_trend:
                avg_trend = sum(spending_trend) / len(spending_trend)
                last_month_spending = float(monthly_spending[-1].total or 0)
                
                # Project next 3 months
                forecast = []
                projected_amount = last_month_spending
                for i in range(3):
                    projected_amount *= (1 + (avg_trend / 100))
                    forecast.append({
                        'month': (datetime.now() + timedelta(days=30 * (i + 1))).strftime('%Y-%m'),
                        'projected_amount': float(projected_amount),
                        'trend_percentage': float(avg_trend)
                    })
            else:
                forecast = []
        else:
            forecast = []
        
        return jsonify({
            'historical_data': [{
                'month': item.month,
                'amount': float(item.total or 0)
            } for item in monthly_spending],
            'forecast': forecast
        })
    except Exception as e:
        print(f"Error in budget forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500
