from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
# from flask_mail import Mail  # Temporarily commented out
from flask_migrate import Migrate
from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
# mail = Mail()  # Temporarily commented out
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    # mail.init_app(app)  # Temporarily commented out
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models
        from app.models import User, Expense, ExpenseCategory, ExpenseSplit, Group, GroupMembership, Settlement
        
        # Register blueprints
        from .routes import (
            auth_bp, main_bp, profile_bp, expense_bp, group_bp,
            settlement_bp, statistics_bp, activity_bp, insights_bp,
            advanced_bp, budget_analytics_bp, category_bp, stats_bp, reports_bp,
            expenses_bp, settlements_bp, budget_bp, recurring_bp, analytics_bp, dashboard_bp
        )
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(profile_bp, url_prefix='/profile')
        app.register_blueprint(expense_bp, url_prefix='/expenses')
        app.register_blueprint(expenses_bp, url_prefix='/expenses')
        app.register_blueprint(group_bp, url_prefix='/groups')
        app.register_blueprint(settlement_bp, url_prefix='/settlements')
        app.register_blueprint(settlements_bp, url_prefix='/settlements')
        app.register_blueprint(statistics_bp, url_prefix='/statistics')
        app.register_blueprint(activity_bp, url_prefix='/activity')
        app.register_blueprint(insights_bp, url_prefix='/insights')
        app.register_blueprint(advanced_bp, url_prefix='/advanced-analytics')
        app.register_blueprint(budget_analytics_bp, url_prefix='/budget-analytics')
        app.register_blueprint(category_bp, url_prefix='/categories')
        app.register_blueprint(stats_bp, url_prefix='/stats')
        app.register_blueprint(reports_bp, url_prefix='/reports')
        app.register_blueprint(budget_bp, url_prefix='/budget')
        app.register_blueprint(recurring_bp, url_prefix='/recurring')
        app.register_blueprint(analytics_bp, url_prefix='/analytics')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        
        # Track user activity
        @app.before_request
        def before_request():
            if current_user.is_authenticated:
                current_user.update_last_active()
        
        # Create database tables
        db.create_all()
        
    return app
