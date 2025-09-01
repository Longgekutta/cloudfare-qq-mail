-- 清理域名数据，只保留shiep.edu.kg
USE cloudfare_qq_mail;

-- 首先删除非shiep.edu.kg域名的用户邮箱
DELETE FROM user_emails 
WHERE domain_id NOT IN (
    SELECT id FROM domains WHERE domain_name = 'shiep.edu.kg'
);

-- 删除非shiep.edu.kg域名的邮件记录
DELETE FROM emails 
WHERE receiver_email NOT LIKE '%@shiep.edu.kg' 
   AND sender_email NOT LIKE '%@shiep.edu.kg';

-- 删除非shiep.edu.kg的域名
DELETE FROM domains 
WHERE domain_name != 'shiep.edu.kg';

-- 确保shiep.edu.kg域名存在
INSERT IGNORE INTO domains (domain_name) VALUES ('shiep.edu.kg');

-- 显示清理结果
SELECT 'Remaining domains:' as info;
SELECT * FROM domains;

SELECT 'Remaining user emails:' as info;
SELECT COUNT(*) as count FROM user_emails;
