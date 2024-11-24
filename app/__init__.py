from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    
    # Import and register blueprints
    from .routes import auth, main, expenses, groups, profile, settlements
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(groups.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(settlements.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
