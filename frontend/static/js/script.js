// 自定义JavaScript代码

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 添加淡入动画效果
    const elements = document.querySelectorAll('.fade-in');
    elements.forEach(function(element) {
        element.style.opacity = '0';
        setTimeout(function() {
            element.style.transition = 'opacity 0.5s ease-in';
            element.style.opacity = '1';
        }, 100);
    });
    
    // 表单验证
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            // 检查必填字段
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    
                    // 创建错误提示
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                        const errorDiv = document.createElement('div');
                        errorDiv.classList.add('invalid-feedback');
                        errorDiv.textContent = '此字段为必填项';
                        field.parentNode.appendChild(errorDiv);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    if (field.nextElementSibling && field.nextElementSibling.classList.contains('invalid-feedback')) {
                        field.nextElementSibling.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                // 滚动到第一个错误字段
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
    
    // 密码强度检查
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(function(field) {
        field.addEventListener('input', function() {
            const password = field.value;
            const strength = checkPasswordStrength(password);
            
            // 移除之前的强度指示器
            const existingIndicator = field.parentNode.querySelector('.password-strength');
            if (existingIndicator) {
                existingIndicator.remove();
            }
            
            // 如果密码不为空，显示强度指示器
            if (password) {
                const strengthIndicator = document.createElement('div');
                strengthIndicator.classList.add('password-strength', 'mt-2');
                strengthIndicator.innerHTML = `
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${strength.percent}%; background-color: ${strength.color};" 
                             aria-valuenow="${strength.percent}" aria-valuemin="0" aria-valuemax="100">
                        </div>
                    </div>
                    <small class="text-muted">密码强度: ${strength.text}</small>
                `;
                field.parentNode.appendChild(strengthIndicator);
            }
        });
    });
    
    // 确认框处理
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = button.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // 模态框处理
    const modalButtons = document.querySelectorAll('[data-bs-toggle="modal"]');
    modalButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const target = button.getAttribute('data-bs-target');
            const modal = document.querySelector(target);
            if (modal) {
                // 清空模态框中的表单
                const form = modal.querySelector('form');
                if (form) {
                    form.reset();
                    // 移除验证错误提示
                    const invalidFields = form.querySelectorAll('.is-invalid');
                    invalidFields.forEach(function(field) {
                        field.classList.remove('is-invalid');
                    });
                    const errorMessages = form.querySelectorAll('.invalid-feedback');
                    errorMessages.forEach(function(message) {
                        message.remove();
                    });
                }
            }
        });
    });
});

// 检查密码强度
function checkPasswordStrength(password) {
    let strength = 0;
    let text = '';
    let color = '';
    
    if (password.length >= 8) strength += 25;
    if (/[a-z]/.test(password)) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;
    
    if (strength < 50) {
        text = '弱';
        color = '#dc3545';
    } else if (strength < 75) {
        text = '中';
        color = '#ffc107';
    } else {
        text = '强';
        color = '#28a745';
    }
    
    return {
        percent: Math.min(strength, 100),
        text: text,
        color: color
    };
}

// AJAX请求封装
function ajaxRequest(url, options) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();
        xhr.open(options.method || 'GET', url);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    resolve(data);
                } catch (e) {
                    reject(new Error('Invalid JSON response'));
                }
            } else {
                reject(new Error('Request failed with status ' + xhr.status));
            }
        };
        
        xhr.onerror = function() {
            reject(new Error('Network error'));
        };
        
        xhr.send(JSON.stringify(options.data || {}));
    });
}

// 显示通知消息
function showNotification(message, type = 'info') {
    // 移除现有的通知
    const existingNotification = document.querySelector('.notification-alert');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // 创建新的通知
    const notification = document.createElement('div');
    notification.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show', 'notification-alert');
    notification.setAttribute('role', 'alert');
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 将通知添加到页面顶部
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // 3秒后自动关闭通知
    setTimeout(function() {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 防抖函数
function debounce(func, wait) {
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

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}