# Personal Finance Tracker

A beautiful and intuitive personal finance tracking application built with Flask and modern web technologies. This project was created for CS50 and helps users manage their income, expenses, and budgets with an elegant user interface.

## Features

### 🎯 Core Functionality
- **User Authentication**: Secure registration and login system
- **Transaction Management**: Track income and expenses with detailed categorization
- **Budget Planning**: Set monthly budgets for different expense categories
- **Financial Dashboard**: Visual overview of your financial health with interactive charts
- **Progress Tracking**: Monitor budget utilization with progress bars and alerts

### 🎨 Beautiful UI/UX
- **Modern Design**: Clean, gradient-based interface with smooth animations
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile devices
- **Interactive Charts**: Beautiful Chart.js visualizations for financial data
- **Intuitive Navigation**: Easy-to-use navigation with clear visual indicators
- **Smart Alerts**: Contextual notifications and budget warnings

### 📊 Financial Insights
- **Monthly Summaries**: Overview of income, expenses, and net balance
- **Category Analysis**: Breakdown of spending by category
- **Trend Visualization**: 6-month financial trend charts
- **Budget vs Actual**: Track how well you're sticking to your budgets

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Bootstrap 5, Custom CSS with gradients and animations
- **Charts**: Chart.js
- **Icons**: Font Awesome

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Quick Start

1. **Clone or navigate to the project directory**
   ```bash
   cd cs50/finance-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   Open your web browser and go to `http://localhost:5000`

## Usage Guide

### Getting Started
1. **Register**: Create a new account with a username, email, and password
2. **Login**: Sign in to access your personal dashboard
3. **Add Transactions**: Start by adding some income and expense transactions
4. **Set Budgets**: Create monthly budgets for different spending categories
5. **Monitor Progress**: Use the dashboard to track your financial progress

### Adding Transactions
- Choose between "Income" or "Expense"
- Select an appropriate category
- Enter the amount and date
- Add an optional description
- Use quick-add buttons for common transaction types

### Managing Budgets
- Set monthly spending limits for categories like Food, Transportation, Entertainment
- Monitor your progress with visual progress bars
- Receive warnings when approaching or exceeding budget limits
- View budget summaries and trends

### Dashboard Features
- **Stats Cards**: Quick overview of total income, expenses, and net balance
- **Financial Chart**: 6-month trend visualization
- **Recent Transactions**: Latest transaction activity
- **Top Categories**: Highest spending categories
- **Quick Actions**: Fast access to add transactions and budgets

## File Structure

```
cs50/finance-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── finance.db            # SQLite database (created automatically)
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Main dashboard
│   ├── transactions.html # Transaction history
│   ├── add_transaction.html # Add transaction form
│   ├── budgets.html      # Budget management
│   └── add_budget.html   # Add budget form
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        └── main.js       # JavaScript utilities
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: User email address
- `password_hash`: Hashed password
- `created_at`: Account creation timestamp

### Transactions Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `type`: Income or expense
- `category`: Transaction category
- `amount`: Transaction amount
- `description`: Optional description
- `date`: Transaction date
- `created_at`: Record creation timestamp

### Budgets Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `category`: Budget category
- `amount`: Budget amount
- `month`: Budget month
- `year`: Budget year
- `created_at`: Record creation timestamp

## Customization

### Adding New Categories
Edit the category lists in:
- `templates/add_transaction.html` (line ~140-170)
- `templates/add_budget.html` (line ~35-45)

### Modifying Colors
Update the CSS variables in `static/css/style.css`:
```css
:root {
    --primary-color: #6366f1;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
}
```

### Changing Chart Appearance
Modify chart configurations in `templates/dashboard.html` and `static/js/main.js`

## Security Features

- **Password Hashing**: Uses Werkzeug's secure password hashing
- **Session Management**: Secure session handling with Flask
- **SQL Injection Protection**: Parameterized queries prevent SQL injection
- **Input Validation**: Client and server-side validation for all forms
- **Authentication Required**: Protected routes require user authentication

## Future Enhancements

Potential features to add:
- **Export Data**: CSV/PDF export functionality
- **Recurring Transactions**: Support for automatic recurring entries
- **Multiple Currencies**: Support for different currencies
- **Advanced Analytics**: More detailed financial reports and insights
- **Goal Setting**: Financial goal tracking and progress monitoring
- **Data Backup**: Cloud backup and sync capabilities

## Contributing

This is a CS50 project, but suggestions and improvements are welcome! Feel free to:
- Report bugs or issues
- Suggest new features
- Improve documentation
- Enhance the user interface

## License

This project is created for educational purposes as part of CS50. Feel free to use and modify for learning purposes.

## Acknowledgments

- **CS50**: Harvard's Introduction to Computer Science course
- **Bootstrap**: For the responsive UI components
- **Chart.js**: For beautiful data visualizations
- **Font Awesome**: For the icon set
- **Flask Community**: For the excellent documentation and examples

---

**Happy budgeting! 💰📊**