from datetime import datetime, timedelta
from sqlalchemy import func, extract
import numpy as np
from sklearn.linear_model import LinearRegression
from ..models import Expense, ExpenseCategory, Group
from .. import db

class ExpenseAnalyzer:
    def __init__(self, user_id):
        self.user_id = user_id

    def get_monthly_trends(self):
        """Analyze monthly expense trends and predict next month's expenses."""
        # Get monthly totals for the past 12 months
        twelve_months_ago = datetime.now() - timedelta(days=365)
        monthly_expenses = db.session.query(
            func.date_trunc('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        ).join(Group, Expense.group_id == Group.id)\
         .join(Group.members)\
         .filter(Group.members.any(user_id=self.user_id))\
         .filter(Expense.date >= twelve_months_ago)\
         .group_by(func.date_trunc('month', Expense.date))\
         .order_by(func.date_trunc('month', Expense.date))\
         .all()

        # Prepare data for prediction
        X = np.array(range(len(monthly_expenses))).reshape(-1, 1)
        y = np.array([amount for _, amount in monthly_expenses])

        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict next month's expenses
        next_month_prediction = model.predict([[len(monthly_expenses)]])[0]

        return {
            'monthly_data': monthly_expenses,
            'prediction': next_month_prediction,
            'trend': model.coef_[0]  # Positive means increasing trend
        }

    def get_category_insights(self):
        """Get detailed insights about spending patterns by category."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Get category expenses
        category_expenses = db.session.query(
            ExpenseCategory.name,
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.id).label('transaction_count'),
            func.avg(Expense.amount).label('avg_amount')
        ).join(Expense)\
         .join(Group, Expense.group_id == Group.id)\
         .join(Group.members)\
         .filter(Group.members.any(user_id=self.user_id))\
         .filter(Expense.date >= thirty_days_ago)\
         .group_by(ExpenseCategory.name)\
         .all()

        # Calculate additional metrics
        insights = []
        for category in category_expenses:
            # Get category trend
            prev_month_total = db.session.query(
                func.sum(Expense.amount)
            ).join(ExpenseCategory)\
             .join(Group, Expense.group_id == Group.id)\
             .join(Group.members)\
             .filter(Group.members.any(user_id=self.user_id))\
             .filter(ExpenseCategory.name == category.name)\
             .filter(Expense.date.between(
                 thirty_days_ago - timedelta(days=30),
                 thirty_days_ago
             ))\
             .scalar() or 0

            month_over_month_change = (
                (category.total_amount - prev_month_total) / prev_month_total * 100
                if prev_month_total > 0 else 0
            )

            insights.append({
                'category': category.name,
                'total_amount': category.total_amount,
                'transaction_count': category.transaction_count,
                'avg_amount': category.avg_amount,
                'month_over_month_change': month_over_month_change
            })

        return insights

    def get_budget_recommendations(self):
        """Generate smart budget recommendations based on spending patterns."""
        insights = self.get_category_insights()
        recommendations = []

        for category in insights:
            # High frequency small transactions
            if category['transaction_count'] > 10 and category['avg_amount'] < 20:
                recommendations.append({
                    'category': category['category'],
                    'type': 'frequency',
                    'message': f"Consider bundling your {category['category']} purchases to reduce transaction frequency."
                })

            # Significant increase in spending
            if category['month_over_month_change'] > 25:
                recommendations.append({
                    'category': category['category'],
                    'type': 'increase',
                    'message': f"Your {category['category']} spending has increased by {category['month_over_month_change']:.1f}% compared to last month."
                })

            # High value category
            if category['total_amount'] > 1000:
                recommendations.append({
                    'category': category['category'],
                    'type': 'high_value',
                    'message': f"Consider setting a budget limit for {category['category']} expenses."
                })

        return recommendations

    def get_savings_opportunities(self):
        """Identify potential savings opportunities."""
        insights = self.get_category_insights()
        opportunities = []

        for category in insights:
            # Look for categories with frequent small transactions
            if category['transaction_count'] > 15 and category['avg_amount'] < 25:
                potential_savings = category['transaction_count'] * 5  # Assume $5 savings per transaction
                opportunities.append({
                    'category': category['category'],
                    'type': 'bulk_purchase',
                    'potential_savings': potential_savings,
                    'message': f"Bulk purchasing in {category['category']} could save up to ${potential_savings:.2f} monthly."
                })

            # Categories with high month-over-month increase
            if category['month_over_month_change'] > 30:
                potential_savings = category['total_amount'] * 0.2  # Assume 20% potential reduction
                opportunities.append({
                    'category': category['category'],
                    'type': 'spending_reduction',
                    'potential_savings': potential_savings,
                    'message': f"Reducing {category['category']} expenses by 20% could save ${potential_savings:.2f} monthly."
                })

        return opportunities

    def get_group_spending_analysis(self):
        """Analyze spending patterns within groups."""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Get group expenses
        group_expenses = db.session.query(
            Group.name,
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.id).label('transaction_count'),
            func.avg(Expense.amount).label('avg_amount')
        ).join(Expense)\
         .join(Group.members)\
         .filter(Group.members.any(user_id=self.user_id))\
         .filter(Expense.date >= thirty_days_ago)\
         .group_by(Group.name)\
         .all()

        analysis = []
        for group in group_expenses:
            # Get expense distribution by category
            category_distribution = db.session.query(
                ExpenseCategory.name,
                func.sum(Expense.amount).label('amount')
            ).join(Expense)\
             .join(Group)\
             .filter(Group.name == group.name)\
             .filter(Expense.date >= thirty_days_ago)\
             .group_by(ExpenseCategory.name)\
             .all()

            analysis.append({
                'group_name': group.name,
                'total_amount': group.total_amount,
                'transaction_count': group.transaction_count,
                'avg_amount': group.avg_amount,
                'category_distribution': {cat: amt for cat, amt in category_distribution}
            })

        return analysis
