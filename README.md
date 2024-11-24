# ExpenseTracker-Pro

## Overview
A comprehensive web application for tracking shared expenses and managing group finances. This application helps users split bills, track expenses, analyze spending patterns, and manage budgets effectively.


![screencapture-localhost-5000-2024-11-24-12_36_24](https://github.com/user-attachments/assets/6bba2033-3e04-445d-8fe9-b7f51848eccf)


## Features

### Core Functionality
- User registration and authentication with secure password handling
- Create and manage groups for shared expenses
- Add expenses with flexible splitting options (equal, percentage, custom)
- Track individual balances and settlements
- Settle up functionality with multiple payment options

### Expense Management
- Categorize expenses with customizable categories
- Add receipts and notes to expenses
- Support for multiple currencies
- Recurring expense management
- Expense history and activity tracking

### Financial Analytics
- Spending pattern analysis
- Budget tracking and alerts
- Category-wise expense breakdown
- Monthly and yearly financial reports
- Trend analysis and insights
- Advanced analytics with spending predictions

### Groups & Social
- Create multiple groups for different purposes
- Add/remove group members
- Group-specific expense tracking
- Group statistics and insights
- Group activity feed

### Budget Management
- Set personal and group budgets
- Category-wise budget allocation
- Budget vs. actual spending analysis
- Budget alerts and notifications
- Budget analytics and recommendations

### Notifications & Alerts
- In-app notifications for expense updates
- Budget threshold alerts
- Settlement reminders
- Spending pattern anomaly detection
- Customizable notification preferences

### Reports & Insights
- Detailed financial reports
- Customizable date ranges
- Export functionality
- Visual analytics with charts and graphs
- Spending insights and recommendations

### User Profile & Preferences
- Manage personal information
- Customize notification settings
- Set default currency and split preferences
- View activity history
- Track login and security information

## Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in `.env`:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///splitwise.db
   FLASK_APP=run.py
   FLASK_ENV=development
   ```
5. Initialize the database:
   ```bash
   flask db upgrade
   ```
6. Run the application:
   ```bash
   flask run
   ```

## Technologies
### Backend
- Flask: Web framework
- SQLAlchemy: ORM and database management
- Flask-Login: User authentication
- Flask-Migrate: Database migrations
- Flask-Bcrypt: Password hashing

### Database
- SQLite (development)
- PostgreSQL (production-ready)

### Frontend
- HTML5 & CSS3
- JavaScript (ES6+)
- Bootstrap 5
- Chart.js for analytics visualization

### Security
- Secure password hashing with Bcrypt
- CSRF protection
- Session management
- Input validation and sanitization

## Project Structure
```
splitwise/
├── app/
│   ├── models/         # Database models
│   ├── routes/         # Route handlers
│   ├── services/       # Business logic
│   ├── static/         # Static files
│   └── templates/      # HTML templates
├── migrations/         # Database migrations
├── tests/             # Test files
├── .env               # Environment variables
├── config.py          # Configuration
├── requirements.txt   # Dependencies
└── run.py            # Application entry point
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request


## Acknowledgments
- Inspired by the original Splitwise application
- Built with modern Python web development best practices
- Focuses on user experience and clean code architecture
