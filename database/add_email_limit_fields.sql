-- 添加邮箱限制相关字段
USE cloudfare_qq_mail;

-- 为用户表添加邮箱注册数量统计字段
ALTER TABLE users 
ADD COLUMN email_registered_count INT DEFAULT 0 COMMENT '已注册邮箱数量（不会因删除而减少）',
ADD COLUMN email_current_count INT DEFAULT 0 COMMENT '当前拥有邮箱数量';

-- 为user_emails表添加是否已删除字段（软删除）
ALTER TABLE user_emails 
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否已删除',
ADD COLUMN deleted_at TIMESTAMP NULL COMMENT '删除时间';

-- 更新现有用户的邮箱数量统计
UPDATE users u SET 
    email_current_count = (
        SELECT COUNT(*) 
        FROM user_emails ue 
        WHERE ue.user_id = u.id AND ue.is_deleted = FALSE
    ),
    email_registered_count = (
        SELECT COUNT(*) 
        FROM user_emails ue 
        WHERE ue.user_id = u.id
    );

-- 创建触发器：当添加新邮箱时自动更新计数
DELIMITER //
CREATE TRIGGER update_email_count_on_insert
AFTER INSERT ON user_emails
FOR EACH ROW
BEGIN
    UPDATE users 
    SET 
        email_registered_count = email_registered_count + 1,
        email_current_count = email_current_count + 1
    WHERE id = NEW.user_id;
END//

-- 创建触发器：当删除邮箱时自动更新当前数量
CREATE TRIGGER update_email_count_on_delete
AFTER UPDATE ON user_emails
FOR EACH ROW
BEGIN
    IF NEW.is_deleted = TRUE AND OLD.is_deleted = FALSE THEN
        UPDATE users 
        SET email_current_count = email_current_count - 1
        WHERE id = NEW.user_id;
    ELSEIF NEW.is_deleted = FALSE AND OLD.is_deleted = TRUE THEN
        UPDATE users 
        SET email_current_count = email_current_count + 1
        WHERE id = NEW.user_id;
    END IF;
END//
DELIMITER ;
