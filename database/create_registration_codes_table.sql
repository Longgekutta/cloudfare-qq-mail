-- 创建注册码表
USE cloudfare_qq_mail;

CREATE TABLE IF NOT EXISTS registration_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE COMMENT '注册码',
    description TEXT COMMENT '注册码描述/备注',
    created_by_user_id INT COMMENT '创建者用户ID',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    is_used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
    used_by_user_id INT COMMENT '使用者用户ID',
    used_at DATETIME COMMENT '使用时间',
    INDEX idx_code (code),
    INDEX idx_is_used (is_used),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (used_by_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='注册码表';




















