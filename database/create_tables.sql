-- 创建数据库
CREATE DATABASE IF NOT EXISTS cloudfare_qq_mail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE cloudfare_qq_mail;

-- 1. 用户数据表：包括用户与管理员的信息
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_vip BOOLEAN DEFAULT FALSE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    vip_expire_date DATETIME NULL,
    monthly_email_count INT DEFAULT 0,
    monthly_reset_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. 域名表：域名名称/该域名下邮箱（支持多个域名）
CREATE TABLE IF NOT EXISTS domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. 邮件表：邮箱发件人/邮箱收件人/邮件内容/邮件发送方发送时间
CREATE TABLE IF NOT EXISTS emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_email VARCHAR(100) NOT NULL,
    receiver_email VARCHAR(100) NOT NULL,
    subject VARCHAR(255),
    content TEXT,
    sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. 用户拥有的邮箱表：用户登录进来创建的自己的邮箱都记录在里面
CREATE TABLE IF NOT EXISTS user_emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_address VARCHAR(100) NOT NULL,
    domain_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_email (user_id, email_address)
);

-- 插入一些示例数据
-- 插入示例域名
INSERT IGNORE INTO domains (domain_name) VALUES 
('shiep.edu.kg'),
('example.com'),
('test.org');

-- 插入示例用户
INSERT IGNORE INTO users (username, password, is_vip, balance) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', TRUE, 100.00),  -- password: admin123
('user1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', FALSE, 50.00);   -- password: admin123

-- 5. 附件表：邮件附件信息
CREATE TABLE IF NOT EXISTS attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
);

-- 6. 充值记录表：记录用户充值和会员购买记录
CREATE TABLE IF NOT EXISTS recharge_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('balance', 'vip') NOT NULL COMMENT '充值类型：余额或会员',
    amount DECIMAL(10, 2) NOT NULL COMMENT '充值金额',
    description VARCHAR(255) DEFAULT '' COMMENT '充值描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. 邮件计费记录表：记录每次邮件发送的费用
CREATE TABLE IF NOT EXISTS email_billing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_id INT NULL,
    cost DECIMAL(10, 4) NOT NULL COMMENT '邮件费用',
    user_type ENUM('normal', 'vip') NOT NULL COMMENT '发送时的用户类型',
    monthly_count INT DEFAULT 0 COMMENT '会员用户当月已发送数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE SET NULL
);

-- 插入示例用户邮箱
INSERT IGNORE INTO user_emails (user_id, email_address, domain_id) VALUES 
(1, 'admin@shiep.edu.kg', 1),
(2, 'user1@example.com', 2);