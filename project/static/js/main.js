// Global utility functions for the Finance Tracker application

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Find or create notification container
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    
    container.innerHTML = alertHtml;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'text-center p-3';
    spinner.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
    element.innerHTML = '';
    element.appendChild(spinner);
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    initializeTooltips();
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    });
    
    // Add smooth scrolling to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// Transaction utilities
const TransactionUtils = {
    // Validate transaction amount
    validateAmount: function(amount) {
        const num = parseFloat(amount);
        return !isNaN(num) && num > 0;
    },
    
    // Get transaction icon based on type
    getTypeIcon: function(type) {
        return type === 'income' ? 'fa-arrow-up' : 'fa-arrow-down';
    },
    
    // Get transaction color class
    getTypeColorClass: function(type) {
        return type === 'income' ? 'income-text' : 'expense-text';
    }
};

// Budget utilities
const BudgetUtils = {
    // Calculate budget progress percentage
    calculateProgress: function(spent, budget) {
        if (budget <= 0) return 0;
        return (spent / budget) * 100;
    },
    
    // Get progress bar color class
    getProgressColorClass: function(percentage) {
        if (percentage <= 75) return 'success';
        if (percentage <= 100) return 'warning';
        return 'danger';
    },
    
    // Get status message
    getStatusMessage: function(spent, budget) {
        const remaining = budget - spent;
        if (remaining < 0) {
            return `Over budget by ${formatCurrency(Math.abs(remaining))}`;
        }
        return `${formatCurrency(remaining)} remaining`;
    }
};

// Chart utilities
const ChartUtils = {
    // Default chart colors
    colors: {
        income: '#10b981',
        expense: '#ef4444',
        primary: '#6366f1',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444'
    },
    
    // Common chart options
    getDefaultOptions: function() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        };
    }
};

// Form utilities
const FormUtils = {
    // Reset form with animation
    resetForm: function(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            form.classList.add('fade-out');
            setTimeout(() => {
                form.classList.remove('fade-out');
                form.classList.add('fade-in');
                setTimeout(() => {
                    form.classList.remove('fade-in');
                }, 300);
            }, 150);
        }
    },
    
    // Validate required fields
    validateRequired: function(formId) {
        const form = document.getElementById(formId);
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    }
};

// Export for use in other scripts
window.FinanceApp = {
    formatCurrency,
    formatDate,
    showNotification,
    showLoading,
    TransactionUtils,
    BudgetUtils,
    ChartUtils,
    FormUtils
};