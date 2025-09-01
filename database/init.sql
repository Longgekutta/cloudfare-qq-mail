-- 邮箱服务数据库初始化脚本
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS cloudfare_qq_mail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cloudfare_qq_mail;

-- 用户表：存储系统用户基本信息
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一标识ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户登录名，唯一标识',
    password VARCHAR(255) NOT NULL COMMENT '用户密码哈希值（bcrypt加密）',
    email VARCHAR(255) NULL COMMENT '用户联系邮箱地址',
    is_vip TINYINT(1) DEFAULT 0 COMMENT 'VIP会员状态：0=普通用户，1=VIP会员',
    is_admin TINYINT(1) DEFAULT 0 COMMENT '管理员权限：0=普通用户，1=管理员',
    balance DECIMAL(10,2) DEFAULT 0.00 COMMENT '用户账户余额（人民币）',
    vip_expire_date DATETIME NULL COMMENT 'VIP会员到期时间',
    monthly_email_count INT DEFAULT 0 COMMENT '当月邮件发送数量统计',
    monthly_reset_date DATE NULL COMMENT '月度统计重置日期',
    vip_email_count INT DEFAULT 0 COMMENT 'VIP用户邮件发送计数',
    vip_start_date DATETIME NULL COMMENT 'VIP会员开始时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '账户创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '账户最后更新时间'
) COMMENT = '系统用户表：存储用户账号、权限、余额等基本信息';

-- 域名表：存储邮箱服务支持的域名
CREATE TABLE IF NOT EXISTS domains (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '域名唯一标识ID',
    domain_name VARCHAR(100) NOT NULL UNIQUE COMMENT '域名名称（如：example.com）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '域名添加时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '域名最后更新时间'
) COMMENT = '邮箱域名表：存储系统支持的邮箱域名列表';

-- 用户邮箱表：存储用户注册的邮箱地址
CREATE TABLE IF NOT EXISTS user_emails (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '邮箱记录唯一标识ID',
    user_id INT NOT NULL COMMENT '邮箱所属用户ID（关联users表）',
    email_address VARCHAR(255) NOT NULL UNIQUE COMMENT '完整邮箱地址（如：user@example.com）',
    domain_id INT NOT NULL COMMENT '邮箱域名ID（关联domains表）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '邮箱注册时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '邮箱最后更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE
) COMMENT = '用户邮箱表：存储用户注册的邮箱地址与域名关联';

-- 邮件表：存储所有邮件的基本信息
CREATE TABLE IF NOT EXISTS emails (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '邮件唯一标识ID',
    sender_email VARCHAR(255) NOT NULL COMMENT '发件人邮箱地址',
    receiver_email VARCHAR(255) NOT NULL COMMENT '收件人邮箱地址',
    subject TEXT COMMENT '邮件主题标题',
    content LONGTEXT COMMENT '邮件正文内容（支持HTML格式）',
    sent_time DATETIME NOT NULL COMMENT '邮件发送时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '邮件记录创建时间',
    INDEX idx_sender (sender_email),
    INDEX idx_receiver (receiver_email),
    INDEX idx_sent_time (sent_time)
) COMMENT = '邮件表：存储系统中所有邮件的基本信息和内容';

-- 附件表：存储邮件附件信息
CREATE TABLE IF NOT EXISTS attachments (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '附件唯一标识ID',
    email_id INT NOT NULL COMMENT '所属邮件ID（关联emails表）',
    filename VARCHAR(255) NOT NULL COMMENT '附件原始文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '附件在服务器上的存储路径',
    file_size BIGINT DEFAULT 0 COMMENT '附件文件大小（字节）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '附件记录创建时间',
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
) COMMENT = '邮件附件表：存储邮件附件的文件信息和路径';

-- 注册码表：存储系统注册码
CREATE TABLE IF NOT EXISTS registration_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    is_used TINYINT(1) DEFAULT 0,
    used_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP NULL,
    FOREIGN KEY (used_by) REFERENCES users(id) ON DELETE SET NULL
) COMMENT = '注册码表：存储用户注册系统的邀请码';

-- 充值码表：存储充值码信息
CREATE TABLE IF NOT EXISTS recharge_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    is_used TINYINT(1) DEFAULT 0,
    used_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP NULL,
    FOREIGN KEY (used_by) REFERENCES users(id) ON DELETE SET NULL
) COMMENT = '充值码表：存储用户充值的兑换码';

-- 用户密码历史表：存储用户密码历史记录
CREATE TABLE IF NOT EXISTS user_password_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plain_password VARCHAR(255) NOT NULL COMMENT '明文密码（仅供管理员查看）',
    hashed_password VARCHAR(255) NOT NULL COMMENT '哈希密码',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 容量超限日志表：记录用户邮箱容量超限情况
CREATE TABLE IF NOT EXISTS capacity_exceeded_log (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志记录唯一标识ID',
    user_id INT NOT NULL COMMENT '超限用户ID（关联users表）',
    exceeded_time DATETIME NOT NULL COMMENT '容量超限发生时间',
    cleanup_time DATETIME NOT NULL COMMENT '计划清理时间（超限后24小时）',
    cleaned TINYINT(1) DEFAULT 0 COMMENT '清理状态：0=未清理，1=已清理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '日志记录创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_cleanup_time (cleanup_time),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) COMMENT = '容量超限日志表：记录用户邮箱容量超限和清理计划';

-- 验证码发送记录表：记录用户验证码发送历史，用于限制发送频率
CREATE TABLE IF NOT EXISTS verification_code_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '验证码发送记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    email VARCHAR(255) NOT NULL COMMENT '目标邮箱',
    code_type VARCHAR(50) NOT NULL COMMENT '验证码类型',
    sent_time DATETIME NOT NULL COMMENT '发送时间',
    ip_address VARCHAR(45) NULL COMMENT '发送IP地址',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_sent_time (sent_time),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) COMMENT = '验证码发送记录表：记录用户验证码发送历史，用于限制发送频率';

-- 插入默认管理员账户
-- 密码: 518107qW (已哈希)
INSERT IGNORE INTO users (username, password, email, is_admin, balance) VALUES
('admin', '$2b$12$sJya6Zec7XpHPj3l6qaNrOFjeVcGCVUoQ5N787ojYcWVDEvXGpmmi', 'admin@system.local', 1, 100.00),
('longgekutta', '$2b$12$nx1ltMhnDvAcatN0uib/l.oC2ioEctS/oDYbN5bDKOfN0VP3uJlw.', 'longgekutta@system.local', 1, 100.00);

-- 插入默认域名
INSERT IGNORE INTO domains (domain_name) VALUES
('shiep.edu.kg'),
('example.com');

-- 插入管理员密码历史记录
INSERT IGNORE INTO user_password_history (user_id, plain_password, hashed_password) VALUES
(1, '518107qW', '$2b$12$sJya6Zec7XpHPj3l6qaNrOFjeVcGCVUoQ5N787ojYcWVDEvXGpmmi'),
(2, '518107qW', '$2b$12$nx1ltMhnDvAcatN0uib/l.oC2ioEctS/oDYbN5bDKOfN0VP3uJlw.');

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_user_emails_user_id ON user_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_user_emails_domain_id ON user_emails(domain_id);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_emails_receiver ON emails(receiver_email);
CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON attachments(email_id);
