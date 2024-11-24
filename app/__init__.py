from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models
        from app.models import User, Expense, ExpenseCategory, ExpenseSplit, Group, GroupMembership, Settlement
        
        # Register blueprints
        from app.routes import auth, main, profile, group, expense, settlement, category, stats, reports
        from app.routes.budget_analytics import bp as budget_analytics_bp
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(main.bp)  # Main blueprint for index and dashboard
        app.register_blueprint(profile.bp, url_prefix='/profile')  # Profile blueprint
        app.register_blueprint(group.bp, url_prefix='/groups')
        app.register_blueprint(expense.bp, url_prefix='/expenses')
        app.register_blueprint(settlement.bp, url_prefix='/settlements')
        app.register_blueprint(category.bp, url_prefix='/categories')
        app.register_blueprint(stats.bp, url_prefix='/stats')  # Stats blueprint
        app.register_blueprint(reports.bp, url_prefix='/reports')  # Reports blueprint
        app.register_blueprint(budget_analytics_bp, url_prefix='/budget-analytics')  # Budget Analytics blueprint
        
        # Track user activity
        @app.before_request
        def before_request():
            if current_user.is_authenticated:
                current_user.update_last_active()
        
        # Create database tables
        db.create_all()
        
    return app
