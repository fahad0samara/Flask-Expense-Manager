from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
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
        from app.routes import auth_bp, main_bp, profile_bp, expense_bp, group_bp, settlement_bp, analytics_bp
        
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(main_bp)
        app.register_blueprint(profile_bp, url_prefix='/profile')
        app.register_blueprint(expense_bp, url_prefix='/expenses')
        app.register_blueprint(group_bp, url_prefix='/groups')
        app.register_blueprint(settlement_bp, url_prefix='/settlements')
        app.register_blueprint(analytics_bp, url_prefix='/analytics')
        
        # Create database tables
        db.create_all()
        
    return app
