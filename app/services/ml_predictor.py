import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
from ..models.expense import Expense
from ..models.user import User
from ..models.group import Group
from sqlalchemy import func
import joblib
import os

class MLPredictor:
    def __init__(self, user_id):
        self.user_id = user_id
        self.model_path = 'app/ml_models'
        os.makedirs(self.model_path, exist_ok=True)
        
    def _prepare_data(self):
        """Prepare historical expense data for ML models"""
        expenses = Expense.query.filter_by(user_id=self.user_id).all()
        
        df = pd.DataFrame([{
            'amount': expense.amount,
            'category': expense.category,
            'date': expense.date,
            'day_of_week': expense.date.weekday(),
            'day_of_month': expense.date.day,
            'month': expense.date.month,
            'group_id': expense.group_id if expense.group_id else -1,
            'is_group_expense': expense.group_id is not None,
            'split_type': expense.split_type
        } for expense in expenses])
        
        return df
        
    def _train_forecast_model(self, df):
        """Train RandomForest model for expense forecasting"""
        X = df[['day_of_week', 'day_of_month', 'month', 'is_group_expense']]
        y = df['amount']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        model_file = os.path.join(self.model_path, f'forecast_model_{self.user_id}.joblib')
        joblib.dump(model, model_file)
        
        return model
        
    def _train_anomaly_detector(self, df):
        """Train IsolationForest for anomaly detection"""
        X = df[['amount', 'day_of_month', 'month']]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X_scaled)
        
        model_file = os.path.join(self.model_path, f'anomaly_model_{self.user_id}.joblib')
        joblib.dump(model, model_file)
        
        return model, scaler
        
    def get_expense_forecasts(self, horizon='6m', granularity='monthly'):
        """Generate expense forecasts using ML model"""
        df = self._prepare_data()
        
        # Load or train forecast model
        model_file = os.path.join(self.model_path, f'forecast_model_{self.user_id}.joblib')
        if os.path.exists(model_file):
            model = joblib.load(model_file)
        else:
            model = self._train_forecast_model(df)
            
        # Generate future dates
        today = datetime.now()
        future_dates = []
        if horizon.endswith('m'):
            months = int(horizon[:-1])
            for i in range(months):
                future_date = today + timedelta(days=30*i)
                future_dates.append({
                    'day_of_week': future_date.weekday(),
                    'day_of_month': future_date.day,
                    'month': future_date.month,
                    'is_group_expense': True
                })
                future_dates.append({
                    'day_of_week': future_date.weekday(),
                    'day_of_month': future_date.day,
                    'month': future_date.month,
                    'is_group_expense': False
                })
                
        future_df = pd.DataFrame(future_dates)
        predictions = model.predict(future_df)
        
        # Aggregate predictions based on granularity
        results = []
        if granularity == 'monthly':
            for i in range(0, len(predictions), 2):
                month = future_dates[i]['month']
                total = predictions[i] + predictions[i+1]
                results.append({
                    'month': month,
                    'predicted_amount': float(total),
                    'group_amount': float(predictions[i]),
                    'personal_amount': float(predictions[i+1])
                })
                
        return results
        
    def get_detailed_forecasts(self):
        """Get detailed forecasts with confidence intervals"""
        forecasts = self.get_expense_forecasts()
        df = self._prepare_data()
        
        # Calculate historical accuracy metrics
        historical_mean = df.groupby('month')['amount'].mean().to_dict()
        historical_std = df.groupby('month')['amount'].std().to_dict()
        
        # Enhance forecasts with confidence intervals
        for forecast in forecasts:
            month = forecast['month']
            if month in historical_std:
                forecast['confidence_interval'] = {
                    'lower': forecast['predicted_amount'] - 2*historical_std[month],
                    'upper': forecast['predicted_amount'] + 2*historical_std[month]
                }
                forecast['historical_mean'] = historical_mean[month]
                forecast['historical_std'] = historical_std[month]
                
        return forecasts
        
    def get_budget_recommendations(self):
        """Generate ML-based budget recommendations"""
        df = self._prepare_data()
        
        # Calculate category-wise statistics
        category_stats = df.groupby('category').agg({
            'amount': ['mean', 'std', 'count']
        }).reset_index()
        
        recommendations = []
        for _, row in category_stats.iterrows():
            category = row['category']
            mean = row['amount']['mean']
            std = row['amount']['std']
            count = row['amount']['count']
            
            if count >= 5:  # Only make recommendations for categories with sufficient data
                recommended_budget = mean + std  # Conservative estimate
                
                recommendations.append({
                    'category': category,
                    'recommended_budget': float(recommended_budget),
                    'average_spend': float(mean),
                    'frequency': int(count),
                    'confidence_score': min(count/10, 1.0),  # Scale confidence based on data points
                    'rationale': f"Based on {count} past transactions with average spend of ${mean:.2f}"
                })
                
        return sorted(recommendations, key=lambda x: x['confidence_score'], reverse=True)
        
    def detect_anomalies(self, recent_expenses):
        """Detect anomalous expenses using IsolationForest"""
        df = self._prepare_data()
        
        # Load or train anomaly detector
        model_file = os.path.join(self.model_path, f'anomaly_model_{self.user_id}.joblib')
        if os.path.exists(model_file):
            model = joblib.load(model_file)
            scaler = StandardScaler()
            scaler.fit(df[['amount', 'day_of_month', 'month']])
        else:
            model, scaler = self._train_anomaly_detector(df)
            
        # Prepare recent expenses for prediction
        X = pd.DataFrame([{
            'amount': expense.amount,
            'day_of_month': expense.date.day,
            'month': expense.date.month
        } for expense in recent_expenses])
        
        X_scaled = scaler.transform(X)
        predictions = model.predict(X_scaled)
        
        # Return anomalous expenses (where prediction is -1)
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                expense = recent_expenses[i]
                anomalies.append({
                    'expense_id': expense.id,
                    'amount': float(expense.amount),
                    'category': expense.category,
                    'date': expense.date.strftime('%Y-%m-%d'),
                    'confidence_score': float(abs(model.score_samples(X_scaled[i:i+1])[0]))
                })
                
        return sorted(anomalies, key=lambda x: x['confidence_score'], reverse=True)
