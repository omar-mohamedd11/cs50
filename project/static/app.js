// Global variables
let transactions = [];
let budgets = [];
let categories = [];
let categoryChart = null;
let monthlyChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load initial data
        await loadCategories();
        await loadTransactions();
        await loadBudgets();
        await loadAnalytics();

        // Set up event listeners
        setupEventListeners();

        // Set default date to today
        document.getElementById('quick-date').value = new Date().toISOString().split('T')[0];
        document.getElementById('transaction-date').value = new Date().toISOString().split('T')[0];

        // Show dashboard by default
        showSection('dashboard');

    } catch (error) {
        console.error('Error initializing app:', error);
        showAlert('Error loading application data', 'danger');
    }
}

// Load categories from API
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        categories = await response.json();
        populateCategories();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Populate category dropdowns
function populateCategories() {
    const selects = ['quick-category', 'transaction-category', 'budget-category'];
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Select Category</option>';
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });
    });
}

// Load transactions from API
async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        transactions = await response.json();
        updateTransactionsDisplay();
        updateRecentTransactions();
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Load budgets from API
async function loadBudgets() {
    try {
        const response = await fetch('/api/budgets');
        budgets = await response.json();
        updateBudgetsDisplay();
    } catch (error) {
        console.error('Error loading budgets:', error);
    }
}

// Load analytics from API
async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const analytics = await response.json();
        updateDashboardStats(analytics);
        updateCharts(analytics);
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Update dashboard statistics
function updateDashboardStats(analytics) {
    document.getElementById('total-income').textContent = formatCurrency(analytics.total_income);
    document.getElementById('total-expenses').textContent = formatCurrency(analytics.total_expenses);
    document.getElementById('net-income').textContent = formatCurrency(analytics.net_income);

    // Update net income card color based on positive/negative
    const netCard = document.querySelector('.net-card');
    if (analytics.net_income >= 0) {
        netCard.style.background = 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)';
    } else {
        netCard.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    }
}

// Update recent transactions display
function updateRecentTransactions() {
    const container = document.getElementById('recent-transactions');
    const recentTransactions = transactions.slice(-5).reverse();

    if (recentTransactions.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent transactions</p>';
        return;
    }

    container.innerHTML = recentTransactions.map(transaction => `
        <div class="transaction-item transaction-${transaction.type}">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${transaction.description}</h6>
                    <small class="text-muted">${formatDate(transaction.date)} • ${transaction.category}</small>
                </div>
                <div class="text-end">
                    <span class="h6 ${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                        ${formatCurrency(transaction.amount)}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
}

// Update transactions table
function updateTransactionsDisplay() {
    const tbody = document.getElementById('transactions-table');

    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No transactions found</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(transaction => `
        <tr>
            <td>${formatDate(transaction.date)}</td>
            <td>${transaction.description}</td>
            <td><span class="badge bg-secondary">${transaction.category}</span></td>
            <td class="${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                ${formatCurrency(transaction.amount)}
            </td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${transaction.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Update budgets display
function updateBudgetsDisplay() {
    const container = document.getElementById('budgets-container');

    if (budgets.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-muted">No budgets set</p></div>';
        return;
    }

    // Calculate spent amounts for each budget
    const spentByCategory = {};
    transactions.forEach(transaction => {
        if (transaction.type === 'expense') {
            const category = transaction.category;
            spentByCategory[category] = (spentByCategory[category] || 0) + Math.abs(transaction.amount);
        }
    });

    container.innerHTML = budgets.map(budget => {
        const spent = spentByCategory[budget.category] || 0;
        const percentage = budget.budget > 0 ? (spent / budget.budget) * 100 : 0;
        const isOverBudget = spent > budget.budget;

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card dashboard-card">
                    <div class="card-body">
                        <h6 class="card-title">${budget.category}</h6>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Spent: ${formatCurrency(spent)}</span>
                            <span>Budget: ${formatCurrency(budget.budget)}</span>
                        </div>
                        <div class="progress mb-2">
                            <div class="progress-bar ${isOverBudget ? 'bg-danger' : 'bg-success'}"
                                 style="width: ${Math.min(percentage, 100)}%">
                            </div>
                        </div>
                        <small class="text-muted">
                            ${percentage.toFixed(1)}% used
                            ${isOverBudget ? `<span class="text-danger">(${formatCurrency(spent - budget.budget)} over)</span>` : ''}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Update charts
function updateCharts(analytics) {
    updateCategoryChart(analytics.category_expenses);
    updateMonthlyChart(analytics.monthly_data);
}

// Update category expenses chart
function updateCategoryChart(categoryExpenses) {
    const ctx = document.getElementById('categoryChart').getContext('2d');

    if (categoryChart) {
        categoryChart.destroy();
    }

    const labels = Object.keys(categoryExpenses);
    const data = Object.values(categoryExpenses);

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                    '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update monthly trends chart
function updateMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthlyChart').getContext('2d');

    if (monthlyChart) {
        monthlyChart.destroy();
    }

    const labels = Object.keys(monthlyData).sort();
    const incomeData = labels.map(month => monthlyData[month].income);
    const expenseData = labels.map(month => monthlyData[month].expenses);

    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Income',
                data: incomeData,
                borderColor: '#43e97b',
                backgroundColor: 'rgba(67, 233, 123, 0.1)',
                fill: false
            }, {
                label: 'Expenses',
                data: expenseData,
                borderColor: '#f5576c',
                backgroundColor: 'rgba(245, 87, 108, 0.1)',
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    // Quick add form
    document.getElementById('quick-add-form').addEventListener('submit', function(e) {
        e.preventDefault();
        addQuickTransaction();
    });

    // Add transaction form
    document.getElementById('add-transaction-form').addEventListener('submit', function(e) {
        e.preventDefault();
        addTransaction();
    });

    // Add budget form
    document.getElementById('add-budget-form').addEventListener('submit', function(e) {
        e.preventDefault();
        addBudget();
    });
}

// Add quick transaction
async function addQuickTransaction() {
    const date = document.getElementById('quick-date').value;
    const description = document.getElementById('quick-description').value;
    const amount = parseFloat(document.getElementById('quick-amount').value);
    const category = document.getElementById('quick-category').value;

    if (!date || !description || !amount || !category) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: date,
                description: description,
                amount: amount,
                category: category
            })
        });

        if (response.ok) {
            document.getElementById('quick-add-form').reset();
            document.getElementById('quick-date').value = new Date().toISOString().split('T')[0];
            await loadTransactions();
            await loadAnalytics();
            showAlert('Transaction added successfully', 'success');
        } else {
            throw new Error('Failed to add transaction');
        }
    } catch (error) {
        console.error('Error adding transaction:', error);
        showAlert('Error adding transaction', 'danger');
    }
}

// Add transaction
async function addTransaction() {
    const date = document.getElementById('transaction-date').value;
    const description = document.getElementById('transaction-description').value;
    const amount = parseFloat(document.getElementById('transaction-amount').value);
    const category = document.getElementById('transaction-category').value;

    if (!date || !description || !amount || !category) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: date,
                description: description,
                amount: amount,
                category: category
            })
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addTransactionModal')).hide();
            document.getElementById('add-transaction-form').reset();
            document.getElementById('transaction-date').value = new Date().toISOString().split('T')[0];
            await loadTransactions();
            await loadAnalytics();
            showAlert('Transaction added successfully', 'success');
        } else {
            throw new Error('Failed to add transaction');
        }
    } catch (error) {
        console.error('Error adding transaction:', error);
        showAlert('Error adding transaction', 'danger');
    }
}

// Add budget
async function addBudget() {
    const category = document.getElementById('budget-category').value;
    const budget = parseFloat(document.getElementById('budget-amount').value);

    if (!category || !budget) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/budgets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: category,
                budget: budget
            })
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addBudgetModal')).hide();
            document.getElementById('add-budget-form').reset();
            await loadBudgets();
            showAlert('Budget set successfully', 'success');
        } else {
            throw new Error('Failed to set budget');
        }
    } catch (error) {
        console.error('Error setting budget:', error);
        showAlert('Error setting budget', 'danger');
    }
}

// Delete transaction
async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    try {
        const response = await fetch(`/api/transactions/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await loadTransactions();
            await loadAnalytics();
            showAlert('Transaction deleted successfully', 'success');
        } else {
            throw new Error('Failed to delete transaction');
        }
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showAlert('Error deleting transaction', 'danger');
    }
}

// Show section
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    document.getElementById(sectionName).style.display = 'block';

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');

    // Load specific data for analytics section
    if (sectionName === 'analytics') {
        loadAnalytics();
    }
}

// Show alert
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// Add mobile menu button functionality
if (window.innerWidth <= 768) {
    const contentArea = document.querySelector('.content-area');
    const menuButton = document.createElement('button');
    menuButton.innerHTML = '<i class="fas fa-bars"></i>';
    menuButton.className = 'btn btn-primary mb-3';
    menuButton.onclick = toggleSidebar;
    contentArea.insertBefore(menuButton, contentArea.firstChild);
}

// Handle window resize
window.addEventListener('resize', function() {
    if (categoryChart) categoryChart.resize();
    if (monthlyChart) monthlyChart.resize();
});
