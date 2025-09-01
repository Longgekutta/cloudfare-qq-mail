-- 待确认支付记录表
CREATE TABLE pending_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    order_id VARCHAR(50) NOT NULL COMMENT '订单号',
    amount DECIMAL(10,2) NOT NULL COMMENT '支付金额',
    payment_type ENUM('balance', 'vip') NOT NULL COMMENT '支付类型：余额充值或会员购买',
    payment_method ENUM('alipay', 'wechat') NOT NULL COMMENT '支付方式：支付宝或微信',
    status ENUM('waiting_auto', 'waiting_manual', 'confirmed', 'cancelled') NOT NULL DEFAULT 'waiting_manual' COMMENT '状态',
    screenshot_path VARCHAR(255) COMMENT '支付截图路径',
    screenshot_filename VARCHAR(255) COMMENT '支付截图文件名',
    admin_note TEXT COMMENT '管理员备注',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    confirmed_at DATETIME COMMENT '确认时间',
    confirmed_by INT COMMENT '确认人用户ID',
    INDEX idx_user_id (user_id),
    INDEX idx_order_id (order_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='待确认支付记录表';
