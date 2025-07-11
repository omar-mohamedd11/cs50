// Optimized Budget Tracker Frontend
class BudgetTracker {
    constructor() {
        this.data = {
            transactions: [],
            budgets: [],
            categories: [],
            analytics: {},
            recentTransactions: []
        };
        this.charts = {
            category: null,
            monthly: null
        };
        this.cache = new Map();
        this.loadingState = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    async init() {
        try {
            this.showLoading(true);
            await this.loadInitialData();
            this.setupEventListeners();
            this.setupDefaultDates();
            this.showSection('dashboard');
            this.showLoading(false);
        } catch (error) {
            console.error('Error initializing app:', error);
            this.showAlert('Failed to initialize application', 'danger');
            this.showLoading(false);
        }
    }
    
    async loadInitialData() {
        try {
            // Use the combined dashboard API for initial load
            const response = await this.fetchWithRetry('/api/dashboard');
            const data = await response.json();
            
            this.data.recentTransactions = data.recent_transactions;
            this.data.analytics = data.analytics;
            this.data.budgets = data.budgets;
            this.data.categories = data.categories;
            
            // Update UI components
            this.updateDashboard();
            this.populateCategories();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            // Fallback to individual API calls
            await this.loadDataFallback();
        }
    }
    
    async loadDataFallback() {
        try {
            const [categoriesRes, analyticsRes, budgetsRes] = await Promise.all([
                this.fetchWithRetry('/api/categories'),
                this.fetchWithRetry('/api/analytics'),
                this.fetchWithRetry('/api/budgets')
            ]);
            
            this.data.categories = await categoriesRes.json();
            this.data.analytics = await analyticsRes.json();
            this.data.budgets = await budgetsRes.json();
            
            // Load recent transactions separately
            const transactionsRes = await this.fetchWithRetry('/api/transactions?no_pagination=true');
            const allTransactions = await transactionsRes.json();
            this.data.recentTransactions = allTransactions.slice(-5).reverse();
            
            this.updateDashboard();
            this.populateCategories();
            
        } catch (error) {
            console.error('Error in fallback data loading:', error);
            throw error;
        }
    }
    
    async fetchWithRetry(url, options = {}) {
        for (let i = 0; i <= this.maxRetries; i++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                this.retryCount = 0; // Reset on success
                return response;
                
            } catch (error) {
                if (i === this.maxRetries) {
                    throw new Error(`Failed after ${this.maxRetries} retries: ${error.message}`);
                }
                
                // Exponential backoff
                const delay = Math.pow(2, i) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    
    setupEventListeners() {
        // Form event listeners with debouncing
        const quickAddForm = document.getElementById('quick-add-form');
        if (quickAddForm) {
            quickAddForm.addEventListener('submit', this.debounce((e) => {
                e.preventDefault();
                this.addQuickTransaction();
            }, 300));
        }
        
        const transactionForm = document.getElementById('add-transaction-form');
        if (transactionForm) {
            transactionForm.addEventListener('submit', this.debounce((e) => {
                e.preventDefault();
                this.addTransaction();
            }, 300));
        }
        
        const budgetForm = document.getElementById('add-budget-form');
        if (budgetForm) {
            budgetForm.addEventListener('submit', this.debounce((e) => {
                e.preventDefault();
                this.addBudget();
            }, 300));
        }
        
        // Navigation with lazy loading
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const section = e.target.getAttribute('onclick')?.match(/'([^']+)'/)?.[1];
                if (section) {
                    e.preventDefault();
                    this.showSection(section);
                }
            });
        });
    }
    
    setupDefaultDates() {
        const today = new Date().toISOString().split('T')[0];
        const quickDate = document.getElementById('quick-date');
        const transactionDate = document.getElementById('transaction-date');
        
        if (quickDate) quickDate.value = today;
        if (transactionDate) transactionDate.value = today;
    }
    
    updateDashboard() {
        this.updateDashboardStats();
        this.updateRecentTransactions();
        this.updateBudgetsDisplay();
        this.updateCharts();
    }
    
    updateDashboardStats() {
        const analytics = this.data.analytics;
        if (!analytics) return;
        
        this.updateElement('total-income', this.formatCurrency(analytics.total_income));
        this.updateElement('total-expenses', this.formatCurrency(analytics.total_expenses));
        this.updateElement('net-income', this.formatCurrency(analytics.net_income));
        
        // Update net income card color
        const netCard = document.querySelector('.net-card');
        if (netCard) {
            netCard.style.background = analytics.net_income >= 0
                ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
                : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        }
    }
    
    updateRecentTransactions() {
        const container = document.getElementById('recent-transactions');
        if (!container) return;
        
        const transactions = this.data.recentTransactions;
        if (!transactions || transactions.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent transactions</p>';
            return;
        }
        
        container.innerHTML = transactions.map(transaction => `
            <div class="transaction-item transaction-${transaction.type}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${this.escapeHtml(transaction.description)}</h6>
                        <small class="text-muted">${this.formatDate(transaction.date)} • ${this.escapeHtml(transaction.category)}</small>
                    </div>
                    <div class="text-end">
                        <span class="h6 ${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                            ${this.formatCurrency(transaction.amount)}
                        </span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    updateBudgetsDisplay() {
        const container = document.getElementById('budgets-container');
        if (!container) return;
        
        const budgets = this.data.budgets;
        if (!budgets || budgets.length === 0) {
            container.innerHTML = '<div class="col-12"><p class="text-muted">No budgets set</p></div>';
            return;
        }
        
        container.innerHTML = budgets.map(budget => {
            const percentage = budget.budget > 0 ? (budget.spent / budget.budget) * 100 : 0;
            const isOverBudget = budget.spent > budget.budget;
            
            return `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card dashboard-card">
                        <div class="card-body">
                            <h6 class="card-title">${this.escapeHtml(budget.category)}</h6>
                            <div class="d-flex justify-content-between mb-2">
                                <span>Spent: ${this.formatCurrency(budget.spent)}</span>
                                <span>Budget: ${this.formatCurrency(budget.budget)}</span>
                            </div>
                            <div class="progress mb-2">
                                <div class="progress-bar ${isOverBudget ? 'bg-danger' : 'bg-success'}"
                                     style="width: ${Math.min(percentage, 100)}%">
                                </div>
                            </div>
                            <small class="text-muted">
                                ${percentage.toFixed(1)}% used
                                ${isOverBudget ? `<span class="text-danger">(${this.formatCurrency(budget.spent - budget.budget)} over)</span>` : ''}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateCharts() {
        if (!this.data.analytics) return;
        
        this.updateCategoryChart(this.data.analytics.category_expenses);
        this.updateMonthlyChart(this.data.analytics.monthly_data);
    }
    
    updateCategoryChart(categoryExpenses) {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.category) {
            this.charts.category.destroy();
        }
        
        const labels = Object.keys(categoryExpenses);
        const data = Object.values(categoryExpenses);
        
        if (labels.length === 0) {
            ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
            return;
        }
        
        this.charts.category = new Chart(ctx.getContext('2d'), {
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
    
    updateMonthlyChart(monthlyData) {
        const ctx = document.getElementById('monthlyChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.monthly) {
            this.charts.monthly.destroy();
        }
        
        const labels = Object.keys(monthlyData).sort();
        const incomeData = labels.map(month => monthlyData[month]?.income || 0);
        const expenseData = labels.map(month => monthlyData[month]?.expenses || 0);
        
        this.charts.monthly = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Income',
                    data: incomeData,
                    borderColor: '#43e97b',
                    backgroundColor: 'rgba(67, 233, 123, 0.1)',
                    fill: false,
                    tension: 0.1
                }, {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: '#f5576c',
                    backgroundColor: 'rgba(245, 87, 108, 0.1)',
                    fill: false,
                    tension: 0.1
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
    
    populateCategories() {
        const selects = ['quick-category', 'transaction-category', 'budget-category'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (!select) return;
            
            select.innerHTML = '<option value="">Select Category</option>';
            this.data.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                select.appendChild(option);
            });
        });
    }
    
    async addQuickTransaction() {
        const formData = this.getFormData('quick-add-form');
        if (!this.validateTransactionData(formData)) return;
        
        try {
            this.setButtonLoading('quick-add-form', true);
            
            const response = await this.fetchWithRetry('/api/transactions', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            // Reset form and refresh data
            document.getElementById('quick-add-form').reset();
            document.getElementById('quick-date').value = new Date().toISOString().split('T')[0];
            
            await this.refreshData();
            this.showAlert('Transaction added successfully', 'success');
            
        } catch (error) {
            console.error('Error adding transaction:', error);
            this.showAlert('Error adding transaction: ' + error.message, 'danger');
        } finally {
            this.setButtonLoading('quick-add-form', false);
        }
    }
    
    async addTransaction() {
        const formData = this.getFormData('add-transaction-form');
        if (!this.validateTransactionData(formData)) return;
        
        try {
            this.setButtonLoading('add-transaction-form', true);
            
            const response = await this.fetchWithRetry('/api/transactions', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            // Close modal and reset form
            const modal = bootstrap.Modal.getInstance(document.getElementById('addTransactionModal'));
            if (modal) modal.hide();
            
            document.getElementById('add-transaction-form').reset();
            document.getElementById('transaction-date').value = new Date().toISOString().split('T')[0];
            
            await this.refreshData();
            this.showAlert('Transaction added successfully', 'success');
            
        } catch (error) {
            console.error('Error adding transaction:', error);
            this.showAlert('Error adding transaction: ' + error.message, 'danger');
        } finally {
            this.setButtonLoading('add-transaction-form', false);
        }
    }
    
    async addBudget() {
        const formData = this.getFormData('add-budget-form');
        if (!this.validateBudgetData(formData)) return;
        
        try {
            this.setButtonLoading('add-budget-form', true);
            
            const response = await this.fetchWithRetry('/api/budgets', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            // Close modal and reset form
            const modal = bootstrap.Modal.getInstance(document.getElementById('addBudgetModal'));
            if (modal) modal.hide();
            
            document.getElementById('add-budget-form').reset();
            
            await this.refreshBudgets();
            this.showAlert('Budget set successfully', 'success');
            
        } catch (error) {
            console.error('Error setting budget:', error);
            this.showAlert('Error setting budget: ' + error.message, 'danger');
        } finally {
            this.setButtonLoading('add-budget-form', false);
        }
    }
    
    async deleteTransaction(id) {
        if (!confirm('Are you sure you want to delete this transaction?')) {
            return;
        }
        
        try {
            await this.fetchWithRetry(`/api/transactions/${id}`, {
                method: 'DELETE'
            });
            
            await this.refreshData();
            this.showAlert('Transaction deleted successfully', 'success');
            
        } catch (error) {
            console.error('Error deleting transaction:', error);
            this.showAlert('Error deleting transaction: ' + error.message, 'danger');
        }
    }
    
    async refreshData() {
        try {
            await this.loadInitialData();
            
            // Refresh transactions table if in transactions section
            const currentSection = document.querySelector('.section:not([style*="display: none"])');
            if (currentSection?.id === 'transactions') {
                await this.loadTransactions();
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }
    
    async refreshBudgets() {
        try {
            const response = await this.fetchWithRetry('/api/budgets');
            this.data.budgets = await response.json();
            this.updateBudgetsDisplay();
        } catch (error) {
            console.error('Error refreshing budgets:', error);
        }
    }
    
    async loadTransactions() {
        try {
            const response = await this.fetchWithRetry('/api/transactions?no_pagination=true');
            const transactions = await response.json();
            this.updateTransactionsTable(transactions);
        } catch (error) {
            console.error('Error loading transactions:', error);
            this.showAlert('Error loading transactions', 'danger');
        }
    }
    
    updateTransactionsTable(transactions) {
        const tbody = document.getElementById('transactions-table');
        if (!tbody) return;
        
        if (!transactions || transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No transactions found</td></tr>';
            return;
        }
        
        tbody.innerHTML = transactions.map(transaction => `
            <tr>
                <td>${this.formatDate(transaction.date)}</td>
                <td>${this.escapeHtml(transaction.description)}</td>
                <td><span class="badge bg-secondary">${this.escapeHtml(transaction.category)}</span></td>
                <td class="${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                    ${this.formatCurrency(transaction.amount)}
                </td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="budgetTracker.deleteTransaction(${transaction.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    async showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`[onclick*="${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
        
        // Lazy load section-specific data
        if (sectionName === 'transactions') {
            await this.loadTransactions();
        } else if (sectionName === 'analytics') {
            // Refresh analytics data
            try {
                const response = await this.fetchWithRetry('/api/analytics');
                this.data.analytics = await response.json();
                this.updateCharts();
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }
    }
    
    // Utility functions
    getFormData(formId) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key.replace(/^(quick-|transaction-|budget-)/, '')] = value;
        }
        
        // Convert amount to float
        if (data.amount) {
            data.amount = parseFloat(data.amount);
        }
        if (data.budget) {
            data.budget = parseFloat(data.budget);
        }
        
        return data;
    }
    
    validateTransactionData(data) {
        if (!data.date || !data.description || !data.amount || !data.category) {
            this.showAlert('Please fill in all fields', 'warning');
            return false;
        }
        
        if (isNaN(data.amount)) {
            this.showAlert('Please enter a valid amount', 'warning');
            return false;
        }
        
        return true;
    }
    
    validateBudgetData(data) {
        if (!data.category || !data.budget) {
            this.showAlert('Please fill in all fields', 'warning');
            return false;
        }
        
        if (isNaN(data.budget) || data.budget <= 0) {
            this.showAlert('Please enter a valid budget amount', 'warning');
            return false;
        }
        
        return true;
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount || 0);
    }
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    }
    
    setButtonLoading(formId, loading) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        const submitBtn = form.querySelector('button[type="submit"]');
        if (!submitBtn) return;
        
        if (loading) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Loading...';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
        }
    }
    
    showLoading(show) {
        this.loadingState = show;
        // Add loading indicator to body if needed
        document.body.style.cursor = show ? 'wait' : 'default';
    }
    
    showAlert(message, type = 'info') {
        // Remove existing alerts
        document.querySelectorAll('.alert.position-fixed').forEach(alert => {
            alert.remove();
        });
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${this.escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize the application
let budgetTracker;
document.addEventListener('DOMContentLoaded', function() {
    budgetTracker = new BudgetTracker();
});

// Legacy support for existing onclick handlers
function showSection(sectionName) {
    if (budgetTracker) {
        budgetTracker.showSection(sectionName);
    }
}

function deleteTransaction(id) {
    if (budgetTracker) {
        budgetTracker.deleteTransaction(id);
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}
