-- 创建邮箱绑定和验证码相关表
USE cloudfare_qq_mail;

-- 1. 用户绑定邮箱表
CREATE TABLE IF NOT EXISTS user_bound_emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_email (user_id, email_address),
    INDEX idx_user_id (user_id),
    INDEX idx_email (email_address)
);

-- 2. 验证码表
CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    code VARCHAR(6) NOT NULL,
    type ENUM('email_binding', 'password_reset', 'login') NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_email (user_id, email_address),
    INDEX idx_code (code),
    INDEX idx_expires (expires_at)
);

-- 3. 验证码发送限制表
CREATE TABLE IF NOT EXISTS verification_limits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    type ENUM('email_binding', 'password_reset', 'login') NOT NULL,
    daily_count INT DEFAULT 0,
    last_sent_at TIMESTAMP NULL,
    reset_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_email_type_date (user_id, email_address, type, reset_date),
    INDEX idx_user_email (user_id, email_address),
    INDEX idx_reset_date (reset_date)
);

-- 4. 邮件发送日志表
CREATE TABLE IF NOT EXISTS email_send_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_email VARCHAR(255) NOT NULL,
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT,
    type ENUM('verification', 'notification', 'system') DEFAULT 'system',
    status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    error_message TEXT NULL,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_to_email (to_email),
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 插入系统发送邮箱配置（如果不存在）
INSERT IGNORE INTO user_emails (user_id, email_address, domain_id) 
SELECT 1, 'longgekutta@shiep.edu.kg', id 
FROM domains 
WHERE domain_name = 'shiep.edu.kg' 
LIMIT 1;
