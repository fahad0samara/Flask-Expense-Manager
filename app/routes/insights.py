from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from ..services.expense_analyzer import ExpenseAnalyzer

insights = Blueprint('insights', __name__)

@insights.route('/insights')
@login_required
def view_insights():
    analyzer = ExpenseAnalyzer(current_user.id)
    
    # Get all insights
    monthly_trends = analyzer.get_monthly_trends()
    category_insights = analyzer.get_category_insights()
    budget_recommendations = analyzer.get_budget_recommendations()
    savings_opportunities = analyzer.get_savings_opportunities()
    group_analysis = analyzer.get_group_spending_analysis()
    
    return render_template('insights/dashboard.html',
                         monthly_trends=monthly_trends,
                         category_insights=category_insights,
                         budget_recommendations=budget_recommendations,
                         savings_opportunities=savings_opportunities,
                         group_analysis=group_analysis)

@insights.route('/api/insights/recommendations')
@login_required
def get_recommendations():
    analyzer = ExpenseAnalyzer(current_user.id)
    recommendations = analyzer.get_budget_recommendations()
    return jsonify(recommendations)

@insights.route('/api/insights/savings')
@login_required
def get_savings():
    analyzer = ExpenseAnalyzer(current_user.id)
    opportunities = analyzer.get_savings_opportunities()
    return jsonify(opportunities)

@insights.route('/api/insights/trends')
@login_required
def get_trends():
    analyzer = ExpenseAnalyzer(current_user.id)
    trends = analyzer.get_monthly_trends()
    return jsonify(trends)
