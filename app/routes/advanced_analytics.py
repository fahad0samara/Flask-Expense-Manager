from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..services.expense_analyzer import ExpenseAnalyzer
from ..services.ml_predictor import MLPredictor
from ..services.notification_service import NotificationService
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

advanced = Blueprint('advanced', __name__)

@advanced.route('/advanced-analytics')
@login_required
def dashboard():
    analyzer = ExpenseAnalyzer(current_user.id)
    ml_predictor = MLPredictor(current_user.id)
    
    # Get comprehensive analytics data
    spending_patterns = analyzer.get_spending_patterns()
    anomaly_detection = analyzer.detect_spending_anomalies()
    expense_forecasts = ml_predictor.get_expense_forecasts()
    peer_comparison = analyzer.get_peer_comparison()
    financial_health = analyzer.calculate_financial_health_score()
    
    return render_template('advanced/dashboard.html',
                         spending_patterns=spending_patterns,
                         anomaly_detection=anomaly_detection,
                         expense_forecasts=expense_forecasts,
                         peer_comparison=peer_comparison,
                         financial_health=financial_health)

@advanced.route('/advanced-analytics/spending-patterns')
@login_required
def spending_patterns():
    analyzer = ExpenseAnalyzer(current_user.id)
    patterns = analyzer.get_detailed_spending_patterns()
    return render_template('advanced/spending_patterns.html', patterns=patterns)

@advanced.route('/advanced-analytics/anomalies')
@login_required
def anomalies():
    analyzer = ExpenseAnalyzer(current_user.id)
    anomalies = analyzer.get_detailed_anomalies()
    return render_template('advanced/anomalies.html', anomalies=anomalies)

@advanced.route('/advanced-analytics/forecasts')
@login_required
def forecasts():
    ml_predictor = MLPredictor(current_user.id)
    forecasts = ml_predictor.get_detailed_forecasts()
    return render_template('advanced/forecasts.html', forecasts=forecasts)

@advanced.route('/advanced-analytics/peer-comparison')
@login_required
def peer_comparison():
    analyzer = ExpenseAnalyzer(current_user.id)
    comparison = analyzer.get_detailed_peer_comparison()
    return render_template('advanced/peer_comparison.html', comparison=comparison)

@advanced.route('/advanced-analytics/financial-health')
@login_required
def financial_health():
    analyzer = ExpenseAnalyzer(current_user.id)
    health_data = analyzer.get_detailed_financial_health()
    return render_template('advanced/financial_health.html', health_data=health_data)

@advanced.route('/api/advanced/spending-patterns')
@login_required
def api_spending_patterns():
    timeframe = request.args.get('timeframe', 'monthly')
    category = request.args.get('category', None)
    
    analyzer = ExpenseAnalyzer(current_user.id)
    patterns = analyzer.get_spending_patterns(timeframe=timeframe, category=category)
    return jsonify(patterns)

@advanced.route('/api/advanced/anomalies')
@login_required
def api_anomalies():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    analyzer = ExpenseAnalyzer(current_user.id)
    anomalies = analyzer.detect_spending_anomalies(start_date=start_date, end_date=end_date)
    return jsonify(anomalies)

@advanced.route('/api/advanced/forecasts')
@login_required
def api_forecasts():
    horizon = request.args.get('horizon', '6m')  # Default 6 months
    granularity = request.args.get('granularity', 'monthly')
    
    ml_predictor = MLPredictor(current_user.id)
    forecasts = ml_predictor.get_expense_forecasts(horizon=horizon, granularity=granularity)
    return jsonify(forecasts)

@advanced.route('/api/advanced/peer-comparison')
@login_required
def api_peer_comparison():
    metric = request.args.get('metric', 'spending')
    timeframe = request.args.get('timeframe', 'monthly')
    
    analyzer = ExpenseAnalyzer(current_user.id)
    comparison = analyzer.get_peer_comparison(metric=metric, timeframe=timeframe)
    return jsonify(comparison)

@advanced.route('/api/advanced/financial-health')
@login_required
def api_financial_health():
    include_history = request.args.get('include_history', 'false') == 'true'
    
    analyzer = ExpenseAnalyzer(current_user.id)
    health_data = analyzer.calculate_financial_health_score(include_history=include_history)
    return jsonify(health_data)

@advanced.route('/advanced-analytics/set-alert', methods=['POST'])
@login_required
def set_alert():
    data = request.get_json()
    alert_type = data.get('type')
    threshold = data.get('threshold')
    notification_method = data.get('notification_method', 'app')  # Changed default to 'app'
    
    notification_service = NotificationService()
    alert_id = notification_service.set_alert(
        user_id=current_user.id,
        alert_type=alert_type,
        threshold=threshold,
        notification_method=notification_method
    )
    return jsonify({'alert_id': alert_id})

@advanced.route('/advanced-analytics/recommendations')
@login_required
def get_recommendations():
    analyzer = ExpenseAnalyzer(current_user.id)
    ml_predictor = MLPredictor(current_user.id)
    
    # Get comprehensive recommendations
    spending_recs = analyzer.get_spending_recommendations()
    saving_recs = analyzer.get_saving_recommendations()
    investment_recs = analyzer.get_investment_recommendations()
    budget_recs = ml_predictor.get_budget_recommendations()
    
    return jsonify({
        'spending': spending_recs,
        'saving': saving_recs,
        'investment': investment_recs,
        'budget': budget_recs
    })
