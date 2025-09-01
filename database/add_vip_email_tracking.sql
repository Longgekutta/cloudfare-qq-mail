-- 添加VIP邮件追踪字段
USE cloudfare_qq_mail;

-- 为用户表添加VIP期间邮件计数字段
ALTER TABLE users 
ADD COLUMN vip_email_count INT DEFAULT 0 COMMENT 'VIP期间已发送邮件数量',
ADD COLUMN vip_start_date DATETIME NULL COMMENT 'VIP开始时间（用于计算免费额度）';

-- 更新现有VIP用户的开始时间（如果有的话）
UPDATE users 
SET vip_start_date = vip_expire_date - INTERVAL 30 DAY
WHERE is_vip = TRUE AND vip_expire_date IS NOT NULL AND vip_start_date IS NULL;

-- 创建邮件发送记录表（如果不存在）
CREATE TABLE IF NOT EXISTS email_send_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_id INT NOT NULL,
    cost DECIMAL(10, 4) DEFAULT 0.0000 COMMENT '邮件发送费用',
    is_vip_free BOOLEAN DEFAULT FALSE COMMENT '是否使用VIP免费额度',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
    INDEX idx_user_sent_at (user_id, sent_at),
    INDEX idx_is_vip_free (is_vip_free)
);

-- 显示更新结果
SELECT 'Updated users table structure:' as info;
DESCRIBE users;
