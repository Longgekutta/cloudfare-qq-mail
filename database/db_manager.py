# -*- coding: utf-8 -*-
"""
数据库管理模块
提供数据库连接和基本操作功能
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("✅ 数据库连接成功")
                return True
                
        except Error as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            print("🔒 数据库连接已关闭")
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        # 检查数据库连接是否有效
        if not self.connection or not self.connection.is_connected():
            print("⚠️ 数据库连接已断开，尝试重新连接...")
            if not self.connect():
                print("❌ 无法重新连接到数据库")
                return None
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            result = self.cursor.fetchall()
            return result
        except Error as e:
            print(f"❌ 查询执行失败: {e}")
            return None
    
    def execute_update(self, query, params=None):
        """执行更新语句（INSERT, UPDATE, DELETE）"""
        # 检查数据库连接是否有效
        if not self.connection or not self.connection.is_connected():
            print("⚠️ 数据库连接已断开，尝试重新连接...")
            if not self.connect():
                print("❌ 无法重新连接到数据库")
                return -1
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            self.connection.commit()
            return self.cursor.rowcount
        except Error as e:
            print(f"❌ 更新执行失败: {e}")
            self.connection.rollback()
            return -1
    
    def create_user(self, username, password, email=None, is_vip=False, is_admin=False, balance=0.0):
        """创建用户，返回用户ID"""
        if email:
            query = "INSERT INTO users (username, password, email, is_vip, is_admin, balance) VALUES (%s, %s, %s, %s, %s, %s)"
            params = (username, password, email, is_vip, is_admin, balance)
        else:
            query = "INSERT INTO users (username, password, is_vip, is_admin, balance) VALUES (%s, %s, %s, %s, %s)"
            params = (username, password, is_vip, is_admin, balance)

        # 检查数据库连接是否有效
        if not self.connection or not self.connection.is_connected():
            print("⚠️ 数据库连接已断开，尝试重新连接...")
            if not self.connect():
                print("❌ 无法重新连接到数据库")
                return -1

        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.lastrowid  # 返回插入的用户ID
        except Error as e:
            print(f"❌ 创建用户失败: {e}")
            self.connection.rollback()
            return -1
    
    def get_user_by_username(self, username):
        """根据用户名获取用户信息"""
        query = "SELECT * FROM users WHERE username = %s"
        params = (username,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        """根据用户ID获取用户信息"""
        query = "SELECT * FROM users WHERE id = %s"
        params = (user_id,)
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def get_user_by_id(self, user_id):
        """根据用户ID获取用户信息"""
        query = "SELECT * FROM users WHERE id = %s"
        params = (user_id,)
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def get_all_domains(self):
        """获取所有域名"""
        query = "SELECT * FROM domains"
        return self.execute_query(query)
    
    def create_domain(self, domain_name):
        """创建域名，返回域名ID"""
        query = "INSERT INTO domains (domain_name) VALUES (%s)"
        params = (domain_name,)
        result = self.execute_update(query, params)
        if result > 0:
            return self.cursor.lastrowid
        return 0

    def get_domain_by_name(self, domain_name):
        """根据域名获取域名信息"""
        query = "SELECT * FROM domains WHERE domain_name = %s"
        params = (domain_name,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def get_domain_by_id(self, domain_id):
        """根据ID获取域名信息"""
        query = "SELECT * FROM domains WHERE id = %s"
        params = (domain_id,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def delete_domain(self, domain_id):
        """删除域名"""
        query = "DELETE FROM domains WHERE id = %s"
        params = (domain_id,)
        return self.execute_update(query, params)

    def update_domain(self, domain_id, domain_name):
        """更新域名"""
        query = "UPDATE domains SET domain_name = %s WHERE id = %s"
        params = (domain_name, domain_id)
        return self.execute_update(query, params)

    def get_emails_by_domain_id(self, domain_id):
        """获取指定域名ID下的所有邮箱"""
        query = "SELECT * FROM user_emails WHERE domain_id = %s"
        params = (domain_id,)
        return self.execute_query(query, params)
    
    def get_user_emails(self, user_id):
        """获取用户的所有邮箱"""
        query = """
        SELECT ue.*, d.domain_name 
        FROM user_emails ue 
        JOIN domains d ON ue.domain_id = d.id 
        WHERE ue.user_id = %s
        """
        params = (user_id,)
        return self.execute_query(query, params)
    
    def check_email_exists(self, email_address, domain_id):
        """检查邮箱是否已存在（同一域名下）"""
        query = "SELECT COUNT(*) as count FROM user_emails WHERE email_address = %s AND domain_id = %s"
        params = (email_address, domain_id)
        result = self.execute_query(query, params)
        return result[0]['count'] > 0 if result else False
    
    def create_user_email(self, user_id, email_address, domain_id):
        """创建用户邮箱"""
        # 首先检查邮箱是否已存在
        if self.check_email_exists(email_address, domain_id):
            return -1  # 返回-1表示邮箱已存在
        
        query = "INSERT INTO user_emails (user_id, email_address, domain_id) VALUES (%s, %s, %s)"
        params = (user_id, email_address, domain_id)
        return self.execute_update(query, params)
    
    def save_email(self, sender_email, receiver_email, subject, content, sent_time):
        """保存邮件信息"""
        query = """
        INSERT INTO emails (sender_email, receiver_email, subject, content, sent_time)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (sender_email, receiver_email, subject, content, sent_time)
        result = self.execute_update(query, params)
        if result > 0:
            # 获取插入的邮件ID
            try:
                self.cursor.execute("SELECT LAST_INSERT_ID()")
                row = self.cursor.fetchone()
                if row:
                    # 检查row是否是字典或元组
                    if isinstance(row, dict):
                        # 如果是字典，尝试获取'id'键
                        email_id = row.get('id', row.get('LAST_INSERT_ID()', 1))
                    elif isinstance(row, (list, tuple)) and len(row) > 0:
                        # 如果是列表或元组，获取第一个元素
                        email_id = row[0]
                    else:
                        # 其他情况返回1
                        email_id = 1
                    return email_id
                else:
                    # 如果没有获取到row，返回1
                    return 1
            except Exception as e:
                print(f"⚠️ 获取邮件ID时出错: {e}")
                return 1

        # 邮件保存成功后，检查相关用户的容量并进行清理
        if result > 0:
            self._check_and_cleanup_user_mailboxes(sender_email, receiver_email)

        return result

    def _check_and_cleanup_user_mailboxes(self, sender_email, receiver_email):
        """检查相关用户的邮箱容量并标记需要清理"""
        try:
            # 获取发件人和收件人的用户ID
            user_ids = set()

            # 查找发件人用户ID
            sender_query = "SELECT user_id FROM user_emails WHERE email_address = %s"
            sender_result = self.execute_query(sender_query, (sender_email,))
            if sender_result:
                for row in sender_result:
                    user_ids.add(row['user_id'])

            # 查找收件人用户ID
            receiver_query = "SELECT user_id FROM user_emails WHERE email_address = %s"
            receiver_result = self.execute_query(receiver_query, (receiver_email,))
            if receiver_result:
                for row in receiver_result:
                    user_ids.add(row['user_id'])

            # 对每个相关用户检查容量并记录超限状态
            for user_id in user_ids:
                usage = self.get_user_mailbox_usage(user_id)
                if usage['total_size_mb'] > 100:
                    # 记录或更新超限状态，但不立即删除
                    self._record_capacity_exceeded(user_id)
                    print(f"📧 用户 {user_id} 邮箱容量超限（{usage['total_size_mb']:.2f}MB），已记录，将在24小时后清理")

        except Exception as e:
            print(f"⚠️ 检查用户邮箱容量时出错: {e}")

    def _record_capacity_exceeded(self, user_id):
        """记录用户容量超限状态"""
        try:
            from datetime import datetime, timedelta

            # 检查是否已有记录
            check_query = "SELECT * FROM capacity_exceeded_log WHERE user_id = %s AND cleaned = 0"
            existing = self.execute_query(check_query, (user_id,))

            if not existing:
                # 创建新的超限记录
                insert_query = """
                INSERT INTO capacity_exceeded_log (user_id, exceeded_time, cleanup_time, cleaned)
                VALUES (%s, %s, %s, 0)
                """
                exceeded_time = datetime.now()
                cleanup_time = exceeded_time + timedelta(hours=24)
                self.execute_update(insert_query, (user_id, exceeded_time, cleanup_time))
                print(f"📝 用户 {user_id} 容量超限记录已创建，将在 {cleanup_time} 清理")

        except Exception as e:
            print(f"⚠️ 记录容量超限状态时出错: {e}")

    def cleanup_expired_mailboxes(self):
        """清理已到期的超限邮箱（定时任务调用）"""
        try:
            from datetime import datetime

            # 查找需要清理的用户
            query = """
            SELECT user_id, exceeded_time FROM capacity_exceeded_log
            WHERE cleaned = 0 AND cleanup_time <= %s
            """
            current_time = datetime.now()
            expired_records = self.execute_query(query, (current_time,))

            if expired_records:
                for record in expired_records:
                    user_id = record['user_id']

                    # 执行清理
                    deleted_count = self.cleanup_user_mailbox(user_id, 100)

                    if deleted_count > 0:
                        # 标记为已清理
                        update_query = "UPDATE capacity_exceeded_log SET cleaned = 1 WHERE user_id = %s AND cleaned = 0"
                        self.execute_update(update_query, (user_id,))
                        print(f"🧹 用户 {user_id} 邮箱已清理 {deleted_count} 封旧邮件")

                print(f"✅ 定时清理完成，处理了 {len(expired_records)} 个用户")

        except Exception as e:
            print(f"⚠️ 定时清理邮箱时出错: {e}")
    
    def get_emails(self, limit=50, offset=0):
        """获取邮件列表"""
        query = "SELECT * FROM emails ORDER BY sent_time DESC LIMIT %s OFFSET %s"
        params = (limit, offset)
        return self.execute_query(query, params)
    
    def get_user_emails_with_isolation(self, user_id, limit=50, offset=0):
        """获取特定用户的邮件列表（实现用户隔离）"""
        query = """
        SELECT e.*, ue.email_address as user_email
        FROM emails e
        JOIN user_emails ue ON (
            e.receiver_email = ue.email_address OR 
            e.sender_email = ue.email_address OR
            e.receiver_email LIKE CONCAT('%<', ue.email_address, '>') OR
            e.sender_email LIKE CONCAT('%<', ue.email_address, '>')
        )
        WHERE ue.user_id = %s
        ORDER BY e.sent_time DESC 
        LIMIT %s OFFSET %s
        """
        params = (user_id, limit, offset)
        return self.execute_query(query, params)
    
    def get_emails_by_domain(self, domain_name, limit=50, offset=0):
        """获取指定域名的邮件"""
        query = """
        SELECT * FROM emails 
        WHERE sender_email LIKE %s OR receiver_email LIKE %s
        ORDER BY sent_time DESC 
        LIMIT %s OFFSET %s
        """
        domain_pattern = f'%@{domain_name}'
        params = (domain_pattern, domain_pattern, limit, offset)
        return self.execute_query(query, params)
    
    def get_user_emails_with_isolation_by_domain(self, user_id, domain_name, limit=50, offset=0):
        """获取与指定用户相关且属于指定域名的邮件"""
        query = """
        SELECT e.*, ue.email_address as user_email
        FROM emails e
        JOIN user_emails ue ON (
            e.receiver_email = ue.email_address OR 
            e.sender_email = ue.email_address OR
            e.receiver_email LIKE CONCAT('%<', ue.email_address, '>') OR
            e.sender_email LIKE CONCAT('%<', ue.email_address, '>')
        )
        WHERE ue.user_id = %s 
        AND (e.sender_email LIKE %s OR e.receiver_email LIKE %s)
        ORDER BY e.sent_time DESC 
        LIMIT %s OFFSET %s
        """
        domain_pattern = f'%@{domain_name}'
        params = (user_id, domain_pattern, domain_pattern, limit, offset)
        return self.execute_query(query, params)
    
    def get_emails_by_email_filter(self, email_filter, limit=50, offset=0):
        """获取包含指定邮箱的邮件（管理员用）"""
        query = """
        SELECT * FROM emails 
        WHERE sender_email = %s OR receiver_email = %s
        ORDER BY sent_time DESC 
        LIMIT %s OFFSET %s
        """
        params = (email_filter, email_filter, limit, offset)
        return self.execute_query(query, params)
    
    def get_emails_count_by_email_filter(self, email_filter):
        """获取包含指定邮箱的邮件总数（管理员用）"""
        query = """
        SELECT COUNT(*) as count FROM emails 
        WHERE sender_email = %s OR receiver_email = %s
        """
        params = (email_filter, email_filter)
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0
    
    def get_emails_count(self):
        """获取所有邮件总数（管理员用）"""
        query = "SELECT COUNT(*) as count FROM emails"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_user_emails_with_isolation_by_email_filter(self, user_id, email_filter, limit=50, offset=0):
        """获取与指定用户相关且包含指定邮箱的邮件"""
        query = """
        SELECT e.*, ue.email_address as user_email
        FROM emails e
        JOIN user_emails ue ON (
            e.receiver_email = ue.email_address OR 
            e.sender_email = ue.email_address OR
            e.receiver_email LIKE CONCAT('%<', ue.email_address, '>') OR
            e.sender_email LIKE CONCAT('%<', ue.email_address, '>')
        )
        WHERE ue.user_id = %s 
        AND ue.email_address = %s
        ORDER BY e.sent_time DESC 
        LIMIT %s OFFSET %s
        """
        params = (user_id, email_filter, limit, offset)
        return self.execute_query(query, params)
    
    def get_user_emails_count_with_isolation_by_email_filter(self, user_id, email_filter):
        """获取与指定用户相关且包含指定邮箱的邮件总数"""
        query = """
        SELECT COUNT(*) as count
        FROM emails e
        JOIN user_emails ue ON (
            e.receiver_email = ue.email_address OR 
            e.sender_email = ue.email_address OR
            e.receiver_email LIKE CONCAT('%<', ue.email_address, '>') OR
            e.sender_email LIKE CONCAT('%<', ue.email_address, '>')
        )
        WHERE ue.user_id = %s 
        AND ue.email_address = %s
        """
        params = (user_id, email_filter)
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0
    
    def get_user_emails_count_with_isolation(self, user_id):
        """获取与指定用户相关的邮件总数"""
        query = """
        SELECT COUNT(*) as count
        FROM emails e
        JOIN user_emails ue ON (
            e.receiver_email = ue.email_address OR 
            e.sender_email = ue.email_address OR
            e.receiver_email LIKE CONCAT('%<', ue.email_address, '>') OR
            e.sender_email LIKE CONCAT('%<', ue.email_address, '>')
        )
        WHERE ue.user_id = %s
        """
        params = (user_id,)
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0
    
    def get_all_user_emails(self):
        """获取所有用户邮箱（管理员用）"""
        query = """
        SELECT DISTINCT ue.email_address, u.username
        FROM user_emails ue
        JOIN users u ON ue.user_id = u.id
        ORDER BY ue.email_address
        """
        return self.execute_query(query)
    
    # 注册码相关方法
    def create_registration_code(self, code, description=None, created_by_user_id=None):
        """创建注册码"""
        query = """
        INSERT INTO registration_codes (code, description, created_by_user_id, created_at, is_used)
        VALUES (%s, %s, %s, NOW(), FALSE)
        """
        params = (code, description, created_by_user_id)
        return self.execute_update(query, params)
    
    def get_registration_codes(self, limit=50, offset=0):
        """获取注册码列表"""
        query = """
        SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
        FROM registration_codes rc
        LEFT JOIN users u ON rc.created_by_user_id = u.id
        LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
        ORDER BY rc.created_at DESC
        LIMIT %s OFFSET %s
        """
        params = (limit, offset)
        return self.execute_query(query, params)
    
    def get_registration_codes_count(self):
        """获取注册码总数"""
        query = "SELECT COUNT(*) as count FROM registration_codes"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_registration_code_by_code(self, code):
        """根据注册码获取详情"""
        query = """
        SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
        FROM registration_codes rc
        LEFT JOIN users u ON rc.created_by_user_id = u.id
        LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
        WHERE rc.code = %s
        """
        params = (code,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def get_registration_code_by_code_for_update(self, code):
        """根据注册码获取详情（带行锁，防止并发使用）"""
        query = """
        SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
        FROM registration_codes rc
        LEFT JOIN users u ON rc.created_by_user_id = u.id
        LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
        WHERE rc.code = %s
        FOR UPDATE
        """
        params = (code,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    # ========== 邮箱绑定相关方法 ==========

    def create_verification_code(self, user_id, email_address, code, code_type, expires_at):
        """创建验证码"""
        query = """
        INSERT INTO verification_codes (user_id, email_address, code, type, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, email_address, code, code_type, expires_at)
        return self.execute_update(query, params)

    def get_verification_code(self, user_id, email_address, code, code_type):
        """获取验证码"""
        query = """
        SELECT * FROM verification_codes
        WHERE user_id = %s AND email_address = %s AND code = %s AND type = %s
        AND is_used = FALSE AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
        """
        params = (user_id, email_address, code, code_type)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def use_verification_code(self, code_id):
        """标记验证码为已使用"""
        query = "UPDATE verification_codes SET is_used = TRUE, used_at = NOW() WHERE id = %s"
        params = (code_id,)
        return self.execute_update(query, params)

    def delete_verification_code(self, code_id):
        """删除验证码"""
        query = "DELETE FROM verification_codes WHERE id = %s"
        params = (code_id,)
        return self.execute_update(query, params)

    def delete_user_verification_codes(self, user_id, email, code_type):
        """删除用户指定邮箱和类型的所有验证码"""
        query = "DELETE FROM verification_codes WHERE user_id = %s AND email_address = %s AND type = %s"
        params = (user_id, email, code_type)
        return self.execute_update(query, params)

    def get_daily_verification_count(self, user_id, email_address, code_type):
        """获取用户今日验证码发送次数"""
        query = """
        SELECT COUNT(*) as count FROM verification_codes
        WHERE user_id = %s AND email_address = %s AND type = %s
        AND DATE(created_at) = CURDATE()
        """
        params = (user_id, email_address, code_type)
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0

    def check_verification_send_limit(self, user_id, email_address, code_type, daily_limit=2):
        """检查验证码发送限制"""
        count = self.get_daily_verification_count(user_id, email_address, code_type)
        return count < daily_limit, count, daily_limit

    def delete_user(self, user_id):
        """删除用户"""
        query = "DELETE FROM users WHERE id = %s"
        params = (user_id,)
        return self.execute_update(query, params)

    def save_password_history(self, user_id, plain_password, hashed_password):
        """保存密码历史记录"""
        query = """
        INSERT INTO user_password_history (user_id, plain_password, hashed_password)
        VALUES (%s, %s, %s)
        """
        params = (user_id, plain_password, hashed_password)
        return self.execute_update(query, params)

    def get_user_latest_password(self, user_id):
        """获取用户最新密码"""
        query = """
        SELECT plain_password FROM user_password_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        params = (user_id,)
        result = self.execute_query(query, params)
        return result[0]['plain_password'] if result else None

    def get_all_emails_for_admin(self, per_page=20, offset=0):
        """管理员获取所有邮件"""
        query = """
        SELECT * FROM emails
        ORDER BY sent_time DESC, id DESC
        LIMIT %s OFFSET %s
        """
        params = (per_page, offset)
        return self.execute_query(query, params)

    def get_all_emails_count_for_admin(self):
        """管理员获取所有邮件总数"""
        query = "SELECT COUNT(*) as count FROM emails"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    def get_admin_created_emails(self, admin_user_id, per_page=20, offset=0):
        """获取管理员创建的邮箱的邮件"""
        query = """
        SELECT e.* FROM emails e
        JOIN user_emails ue ON (e.sender_email = ue.email_address OR e.receiver_email = ue.email_address)
        WHERE ue.created_by = %s
        ORDER BY e.sent_time DESC, e.id DESC
        LIMIT %s OFFSET %s
        """
        params = (admin_user_id, per_page, offset)
        return self.execute_query(query, params)

    def get_admin_created_emails_count(self, admin_user_id):
        """获取管理员创建的邮箱的邮件总数"""
        query = """
        SELECT COUNT(DISTINCT e.id) as count FROM emails e
        JOIN user_emails ue ON (e.sender_email = ue.email_address OR e.receiver_email = ue.email_address)
        WHERE ue.created_by = %s
        """
        params = (admin_user_id,)
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0

    def get_verification_limit(self, user_id, email_address, code_type):
        """获取验证码发送限制"""
        query = """
        SELECT * FROM verification_limits
        WHERE user_id = %s AND email_address = %s AND type = %s AND reset_date = CURDATE()
        """
        params = (user_id, email_address, code_type)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def update_verification_limit(self, user_id, email_address, code_type):
        """更新验证码发送限制"""
        query = """
        INSERT INTO verification_limits (user_id, email_address, type, daily_count, last_sent_at, reset_date)
        VALUES (%s, %s, %s, 1, NOW(), CURDATE())
        ON DUPLICATE KEY UPDATE
        daily_count = daily_count + 1,
        last_sent_at = NOW()
        """
        params = (user_id, email_address, code_type)
        return self.execute_update(query, params)

    def add_bound_email(self, user_id, email_address):
        """添加绑定邮箱"""
        query = """
        INSERT INTO user_bound_emails (user_id, email_address, is_verified, verified_at)
        VALUES (%s, %s, TRUE, NOW())
        """
        params = (user_id, email_address)
        return self.execute_update(query, params)

    def get_bound_emails(self, user_id):
        """获取用户绑定的邮箱"""
        query = "SELECT * FROM user_bound_emails WHERE user_id = %s AND is_verified = TRUE"
        params = (user_id,)
        return self.execute_query(query, params)

    def get_user_by_bound_email(self, email_address):
        """通过绑定邮箱获取用户"""
        query = """
        SELECT u.* FROM users u
        JOIN user_bound_emails ube ON u.id = ube.user_id
        WHERE ube.email_address = %s AND ube.is_verified = TRUE
        """
        params = (email_address,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    def update_user_password(self, user_id, new_password_hash):
        """更新用户密码"""
        query = "UPDATE users SET password = %s WHERE id = %s"
        params = (new_password_hash, user_id)
        return self.execute_update(query, params)

    def update_user_vip_status(self, user_id, is_vip, expire_date=None, reset_count=True):
        """更新用户VIP状态"""
        from datetime import datetime

        if is_vip and expire_date:
            if reset_count:
                # 新购买VIP，重置计数和开始时间
                query = """
                UPDATE users
                SET is_vip = %s, vip_expire_date = %s, vip_email_count = 0, vip_start_date = %s
                WHERE id = %s
                """
                params = (is_vip, expire_date, datetime.now(), user_id)
            else:
                # 续费VIP，只更新到期时间，不重置计数
                query = """
                UPDATE users
                SET is_vip = %s, vip_expire_date = %s
                WHERE id = %s
                """
                params = (is_vip, expire_date, user_id)
        else:
            # 取消VIP状态
            query = """
            UPDATE users
            SET is_vip = %s, vip_expire_date = NULL, vip_email_count = 0, vip_start_date = NULL
            WHERE id = %s
            """
            params = (is_vip, user_id)
        return self.execute_update(query, params)

    def get_vip_email_count(self, user_id):
        """获取用户VIP期间已发送邮件数量"""
        query = "SELECT vip_email_count FROM users WHERE id = %s"
        params = (user_id,)
        result = self.execute_query(query, params)
        return result[0]['vip_email_count'] if result else 0

    def increment_vip_email_count(self, user_id):
        """增加用户VIP期间邮件计数"""
        query = "UPDATE users SET vip_email_count = vip_email_count + 1 WHERE id = %s"
        params = (user_id,)
        return self.execute_update(query, params)

    def add_email_send_record(self, user_id, email_id, cost, is_vip_free=False):
        """添加邮件发送记录"""
        query = """
        INSERT INTO email_send_records (user_id, email_id, cost, is_vip_free)
        VALUES (%s, %s, %s, %s)
        """
        params = (user_id, email_id, cost, is_vip_free)
        return self.execute_update(query, params)
    
    def use_registration_code(self, code, user_id):
        """使用注册码"""
        query = """
        UPDATE registration_codes
        SET is_used = TRUE, used_by_user_id = %s, used_at = NOW()
        WHERE code = %s AND is_used = FALSE
        """
        params = (user_id, code)
        return self.execute_update(query, params)
    
    def delete_registration_code(self, code):
        """删除注册码"""
        query = "DELETE FROM registration_codes WHERE code = %s"
        params = (code,)
        return self.execute_update(query, params)

    def delete_used_registration_codes(self):
        """批量删除所有已使用的注册码"""
        query = "DELETE FROM registration_codes WHERE is_used = TRUE"
        result = self.execute_update(query)
        return result if result > 0 else 0

    def register_user_with_code(self, username, password, registration_code):
        """使用注册码注册用户（原子操作）"""
        if not self.connection or not self.connection.is_connected():
            print("⚠️ 数据库连接已断开，尝试重新连接...")
            if not self.connect():
                print("❌ 无法重新连接到数据库")
                return {'success': False, 'message': '数据库连接失败'}

        try:
            # 设置自动提交为False，开始事务
            self.connection.autocommit = False

            # 1. 锁定并检查注册码
            query = """
            SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
            FROM registration_codes rc
            LEFT JOIN users u ON rc.created_by_user_id = u.id
            LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
            WHERE rc.code = %s
            FOR UPDATE
            """
            self.cursor.execute(query, (registration_code,))
            reg_code_info = self.cursor.fetchone()

            if not reg_code_info:
                self.connection.rollback()
                return {'success': False, 'message': '注册码不存在或无效'}

            if reg_code_info['is_used']:
                self.connection.rollback()
                return {'success': False, 'message': '注册码已被使用'}

            # 2. 检查用户名是否已存在
            query = "SELECT id FROM users WHERE username = %s"
            self.cursor.execute(query, (username,))
            existing_user = self.cursor.fetchone()

            if existing_user:
                self.connection.rollback()
                return {'success': False, 'message': '用户名已存在'}

            # 3. 创建用户
            query = "INSERT INTO users (username, password, is_vip, balance) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(query, (username, password, False, 0.0))
            user_id = self.cursor.lastrowid

            if not user_id:
                self.connection.rollback()
                return {'success': False, 'message': '用户创建失败'}

            # 4. 保存密码历史
            from app import hash_password
            plain_password = password  # 这里应该传入明文密码
            query = """
            INSERT INTO user_password_history (user_id, plain_password, hashed_password)
            VALUES (%s, %s, %s)
            """
            self.cursor.execute(query, (user_id, plain_password, password))

            # 5. 标记注册码为已使用
            query = """
            UPDATE registration_codes
            SET is_used = TRUE, used_by_user_id = %s, used_at = NOW()
            WHERE code = %s AND is_used = FALSE
            """
            self.cursor.execute(query, (user_id, registration_code))

            if self.cursor.rowcount == 0:
                self.connection.rollback()
                return {'success': False, 'message': '注册码使用失败，可能已被其他用户使用'}

            # 提交事务
            self.connection.commit()
            # 恢复自动提交
            self.connection.autocommit = True

            return {
                'success': True,
                'message': '注册成功',
                'user_id': user_id,
                'username': username
            }

        except Error as e:
            self.connection.rollback()
            # 恢复自动提交
            self.connection.autocommit = True
            print(f"❌ 注册用户失败: {e}")
            return {'success': False, 'message': f'注册过程出现异常: {str(e)}'}
        except Exception as e:
            self.connection.rollback()
            # 恢复自动提交
            self.connection.autocommit = True
            print(f"❌ 注册用户异常: {e}")
            return {'success': False, 'message': f'注册过程出现异常: {str(e)}'}

    # ========== 充值码管理方法 ==========

    def create_recharge_code(self, code, amount, description, created_by_user_id):
        """创建充值码"""
        query = """
        INSERT INTO recharge_codes (code, amount, description, created_by_user_id)
        VALUES (%s, %s, %s, %s)
        """
        params = (code, amount, description, created_by_user_id)
        return self.execute_update(query, params)

    def get_recharge_codes(self, limit=20, offset=0, amount_filter=None):
        """获取充值码列表"""
        if amount_filter:
            query = """
            SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
            FROM recharge_codes rc
            LEFT JOIN users u ON rc.created_by_user_id = u.id
            LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
            WHERE rc.amount = %s
            ORDER BY rc.created_at DESC
            LIMIT %s OFFSET %s
            """
            params = (amount_filter, limit, offset)
        else:
            query = """
            SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
            FROM recharge_codes rc
            LEFT JOIN users u ON rc.created_by_user_id = u.id
            LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
            ORDER BY rc.created_at DESC
            LIMIT %s OFFSET %s
            """
            params = (limit, offset)
        return self.execute_query(query, params)

    def get_recharge_codes_count(self, amount_filter=None):
        """获取充值码总数"""
        if amount_filter:
            query = "SELECT COUNT(*) as count FROM recharge_codes WHERE amount = %s"
            params = (amount_filter,)
        else:
            query = "SELECT COUNT(*) as count FROM recharge_codes"
            params = ()
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0

    def get_unused_recharge_codes_by_amount(self, amount):
        """获取指定面额的所有未使用充值码"""
        query = """
        SELECT code FROM recharge_codes
        WHERE amount = %s AND is_used = FALSE
        ORDER BY created_at ASC
        """
        params = (amount,)
        result = self.execute_query(query, params)
        return [row['code'] for row in result] if result else []

    def get_unused_registration_codes(self):
        """获取所有未使用的注册码"""
        query = """
        SELECT code FROM registration_codes
        WHERE is_used = FALSE
        ORDER BY created_at ASC
        """
        result = self.execute_query(query)
        return [row['code'] for row in result] if result else []

    def delete_recharge_code(self, code):
        """删除充值码"""
        query = "DELETE FROM recharge_codes WHERE code = %s"
        params = (code,)
        return self.execute_update(query, params)

    def delete_used_recharge_codes(self):
        """批量删除所有已使用的充值码"""
        query = "DELETE FROM recharge_codes WHERE is_used = TRUE"
        result = self.execute_update(query)
        return result if result > 0 else 0

    def use_recharge_code(self, code, user_id):
        """使用充值码"""
        query = """
        UPDATE recharge_codes
        SET is_used = TRUE, used_by_user_id = %s, used_at = NOW()
        WHERE code = %s AND is_used = FALSE
        """
        params = (user_id, code)
        return self.execute_update(query, params)

    def get_recharge_code_by_code(self, code):
        """根据充值码获取详情"""
        query = """
        SELECT rc.*, u.username as created_by_username, u2.username as used_by_username
        FROM recharge_codes rc
        LEFT JOIN users u ON rc.created_by_user_id = u.id
        LEFT JOIN users u2 ON rc.used_by_user_id = u2.id
        WHERE rc.code = %s
        """
        params = (code,)
        result = self.execute_query(query, params)
        return result[0] if result else None

    # ========== 邮箱容量管理方法 ==========

    def get_user_mailbox_usage(self, user_id):
        """获取用户邮箱使用情况"""
        query = """
        SELECT
            COUNT(e.id) as email_count,
            COALESCE(SUM(LENGTH(e.subject) + LENGTH(e.content)), 0) as email_size,
            COALESCE(SUM(a.file_size), 0) as attachment_size,
            COALESCE(SUM(LENGTH(e.subject) + LENGTH(e.content)), 0) + COALESCE(SUM(a.file_size), 0) as total_size
        FROM emails e
        LEFT JOIN user_emails ue ON (e.sender_email = ue.email_address OR e.receiver_email = ue.email_address)
        LEFT JOIN attachments a ON e.id = a.email_id
        WHERE ue.user_id = %s
        """
        params = (user_id,)
        result = self.execute_query(query, params)
        if result:
            usage = result[0]
            return {
                'email_count': usage['email_count'] or 0,
                'email_size': usage['email_size'] or 0,
                'attachment_size': usage['attachment_size'] or 0,
                'total_size': usage['total_size'] or 0,
                'total_size_mb': round((usage['total_size'] or 0) / (1024 * 1024), 2)
            }
        return {
            'email_count': 0,
            'email_size': 0,
            'attachment_size': 0,
            'total_size': 0,
            'total_size_mb': 0.0
        }

    def get_user_oldest_emails(self, user_id, limit=10):
        """获取用户最旧的邮件（用于清理）"""
        query = """
        SELECT DISTINCT e.id, e.sent_time,
               LENGTH(e.subject) + LENGTH(e.content) as email_size,
               COALESCE(SUM(a.file_size), 0) as attachment_size
        FROM emails e
        LEFT JOIN user_emails ue ON (e.sender_email = ue.email_address OR e.receiver_email = ue.email_address)
        LEFT JOIN attachments a ON e.id = a.email_id
        WHERE ue.user_id = %s
        GROUP BY e.id, e.sent_time
        ORDER BY e.sent_time ASC
        LIMIT %s
        """
        params = (user_id, limit)
        return self.execute_query(query, params)

    def get_email_attachments(self, email_id):
        """获取邮件的附件列表"""
        query = "SELECT * FROM attachments WHERE email_id = %s"
        params = (email_id,)
        return self.execute_query(query, params) or []

    def delete_email_and_attachments(self, email_id):
        """删除邮件及其附件"""
        try:
            # 先删除附件文件
            attachments = self.get_email_attachments(email_id)
            for attachment in attachments:
                file_path = attachment.get('file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除附件文件失败: {file_path}, 错误: {e}")

            # 删除数据库记录
            self.execute_update("DELETE FROM attachments WHERE email_id = %s", (email_id,))
            result = self.execute_update("DELETE FROM emails WHERE id = %s", (email_id,))
            return result > 0
        except Exception as e:
            print(f"删除邮件失败: {e}")
            return False

    def cleanup_user_mailbox(self, user_id, target_size_mb=100):
        """清理用户邮箱到指定大小"""
        target_size_bytes = target_size_mb * 1024 * 1024
        deleted_count = 0

        while True:
            # 检查当前使用量
            usage = self.get_user_mailbox_usage(user_id)
            if usage['total_size'] <= target_size_bytes:
                break

            # 获取最旧的邮件
            oldest_emails = self.get_user_oldest_emails(user_id, 5)
            if not oldest_emails:
                break

            # 删除最旧的邮件
            for email in oldest_emails:
                if self.delete_email_and_attachments(email['id']):
                    deleted_count += 1

                # 再次检查容量
                usage = self.get_user_mailbox_usage(user_id)
                if usage['total_size'] <= target_size_bytes:
                    break

            # 防止无限循环
            if deleted_count > 100:
                break

        return deleted_count

    # ========== 验证码发送限制管理 ==========

    def check_verification_code_limit(self, user_id, email=None, daily_limit=2):
        """检查用户今日验证码发送次数是否超限"""
        try:
            from datetime import datetime, date
            today = date.today()

            # 构建查询条件
            if email:
                # 按邮箱地址限制
                query = """
                SELECT COUNT(*) as count FROM verification_code_logs
                WHERE email = %s AND DATE(sent_time) = %s
                """
                params = (email, today)
            else:
                # 按用户ID限制
                query = """
                SELECT COUNT(*) as count FROM verification_code_logs
                WHERE user_id = %s AND DATE(sent_time) = %s
                """
                params = (user_id, today)

            result = self.execute_query(query, params)
            if result:
                count = result[0]['count']
                return count < daily_limit, count
            return True, 0

        except Exception as e:
            print(f"⚠️ 检查验证码发送限制时出错: {e}")
            return True, 0  # 出错时允许发送

    def log_verification_code_sent(self, user_id, email, code_type, ip_address=None):
        """记录验证码发送日志"""
        try:
            from datetime import datetime

            query = """
            INSERT INTO verification_code_logs (user_id, email, code_type, sent_time, ip_address)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (user_id, email, code_type, datetime.now(), ip_address)
            result = self.execute_update(query, params)
            return result > 0

        except Exception as e:
            print(f"⚠️ 记录验证码发送日志时出错: {e}")
            return False

    def get_user_verification_code_stats(self, user_id):
        """获取用户验证码发送统计"""
        try:
            from datetime import datetime, date
            today = date.today()

            query = """
            SELECT
                COUNT(*) as today_count,
                MAX(sent_time) as last_sent_time
            FROM verification_code_logs
            WHERE user_id = %s AND DATE(sent_time) = %s
            """
            params = (user_id, today)
            result = self.execute_query(query, params)

            if result:
                return {
                    'today_count': result[0]['today_count'] or 0,
                    'last_sent_time': result[0]['last_sent_time'],
                    'remaining_count': max(0, 2 - (result[0]['today_count'] or 0))
                }
            return {'today_count': 0, 'last_sent_time': None, 'remaining_count': 2}

        except Exception as e:
            print(f"⚠️ 获取验证码发送统计时出错: {e}")
            return {'today_count': 0, 'last_sent_time': None, 'remaining_count': 2}

    def get_user_inbox_emails(self, user_id, limit=50, offset=0):
        """获取特定用户的收件邮件列表"""
        query = """
        SELECT e.*, ue.email_address as user_email
        FROM emails e
        JOIN user_emails ue ON e.receiver_email = ue.email_address
        WHERE ue.user_id = %s
        ORDER BY e.sent_time DESC 
        LIMIT %s OFFSET %s
        """
        params = (user_id, limit, offset)
        return self.execute_query(query, params)
    
    def get_user_outbox_emails(self, user_id, limit=50, offset=0):
        """获取特定用户的发件邮件列表"""
        query = """
        SELECT e.*, ue.email_address as user_email
        FROM emails e
        JOIN user_emails ue ON e.sender_email = ue.email_address
        WHERE ue.user_id = %s
        ORDER BY e.sent_time DESC 
        LIMIT %s OFFSET %s
        """
        params = (user_id, limit, offset)
        return self.execute_query(query, params)
    
    def get_email_by_id(self, email_id):
        """根据ID获取邮件详情"""
        query = "SELECT * FROM emails WHERE id = %s"
        params = (email_id,)
        result = self.execute_query(query, params)
        if result:
            email = result[0]
            # 获取附件信息
            attachments = self.get_attachments_by_email_id(email_id)
            email['attachments'] = attachments if attachments is not None else []
            return email
        return None
    
    def get_user_email_by_id_with_isolation(self, email_id, user_id):
        """根据ID获取特定用户的邮件详情（实现用户隔离）"""
        query = """
        SELECT e.*, ue.email_address as user_email
        FROM emails e
        JOIN user_emails ue ON (
            e.receiver_email = ue.email_address OR 
            e.sender_email = ue.email_address OR
            e.receiver_email LIKE CONCAT('%<', ue.email_address, '>') OR
            e.sender_email LIKE CONCAT('%<', ue.email_address, '>')
        )
        WHERE e.id = %s AND ue.user_id = %s
        """
        params = (email_id, user_id)
        result = self.execute_query(query, params)
        if result:
            email = result[0]
            # 获取附件信息
            attachments = self.get_attachments_by_email_id(email_id)
            email['attachments'] = attachments if attachments is not None else []
            return email
        return None
    
    def get_all_users(self):
        """获取所有用户，包含最新密码"""
        query = """
        SELECT u.*,
               (SELECT ph.plain_password
                FROM user_password_history ph
                WHERE ph.user_id = u.id
                ORDER BY ph.created_at DESC
                LIMIT 1) as latest_password
        FROM users u
        ORDER BY u.id
        """
        return self.execute_query(query)
    
    def update_user(self, user_id, username, email, is_vip, balance, is_admin=None):
        """更新用户信息"""
        if is_admin is not None:
            query = "UPDATE users SET username=%s, email=%s, is_vip=%s, balance=%s, is_admin=%s WHERE id=%s"
            params = (username, email, is_vip, balance, is_admin, user_id)
        else:
            query = "UPDATE users SET username=%s, email=%s, is_vip=%s, balance=%s WHERE id=%s"
            params = (username, email, is_vip, balance, user_id)
        return self.execute_update(query, params)
    
    def delete_user(self, user_id):
        """删除用户"""
        query = "DELETE FROM users WHERE id=%s"
        params = (user_id,)
        return self.execute_update(query, params)
    
    def create_attachment(self, email_id, filename, file_path, file_size):
        """创建附件记录"""
        query = """
        INSERT INTO attachments (email_id, filename, file_path, file_size) 
        VALUES (%s, %s, %s, %s)
        """
        params = (email_id, filename, file_path, file_size)
        return self.execute_update(query, params)
    
    def get_attachments_by_email_id(self, email_id):
        """根据邮件ID获取附件列表"""
        query = "SELECT * FROM attachments WHERE email_id = %s"
        params = (email_id,)
        return self.execute_query(query, params)
    
    def get_attachment_by_id(self, attachment_id):
        """根据ID获取附件详情"""
        query = "SELECT * FROM attachments WHERE id = %s"
        params = (attachment_id,)
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    # 会员和充值相关方法
    def update_user_balance(self, user_id, amount):
        """更新用户余额（增加金额）"""
        query = "UPDATE users SET balance = balance + %s WHERE id = %s"
        params = (amount, user_id)
        return self.execute_update(query, params)

    def set_user_balance(self, user_id, balance):
        """设置用户余额（绝对值）"""
        query = "UPDATE users SET balance = %s WHERE id = %s"
        params = (balance, user_id)
        return self.execute_update(query, params)
    
    def set_user_vip(self, user_id, expire_date):
        """设置用户会员状态和过期时间"""
        query = """
        UPDATE users SET 
            is_vip = TRUE, 
            vip_expire_date = %s,
            monthly_email_count = 0,
            monthly_reset_date = CURDATE()
        WHERE id = %s
        """
        params = (expire_date, user_id)
        return self.execute_update(query, params)
    
    def check_and_update_vip_status(self, user_id):
        """检查并更新会员状态（如果过期则取消）"""
        from datetime import datetime
        query = """
        UPDATE users SET 
            is_vip = FALSE, 
            vip_expire_date = NULL
        WHERE id = %s AND vip_expire_date IS NOT NULL AND vip_expire_date < NOW()
        """
        params = (user_id,)
        self.execute_update(query, params)
        
        # 返回当前会员状态
        user = self.get_user_by_id(user_id)
        return user.get('is_vip', False) if user else False
    
    def reset_monthly_email_count_if_needed(self, user_id):
        """如果需要，重置月度邮件计数"""
        from datetime import date
        query = """
        UPDATE users SET 
            monthly_email_count = 0,
            monthly_reset_date = CURDATE()
        WHERE id = %s AND (monthly_reset_date IS NULL OR monthly_reset_date < CURDATE())
        """
        params = (user_id,)
        return self.execute_update(query, params)
    
    def increment_monthly_email_count(self, user_id):
        """增加月度邮件计数"""
        query = "UPDATE users SET monthly_email_count = monthly_email_count + 1 WHERE id = %s"
        params = (user_id,)
        return self.execute_update(query, params)
    
    def get_user_monthly_stats(self, user_id):
        """获取用户月度统计"""
        query = """
        SELECT monthly_email_count, monthly_reset_date, is_vip, vip_expire_date, balance
        FROM users WHERE id = %s
        """
        params = (user_id,)
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def calculate_email_cost(self, user_id):
        """计算邮件发送费用"""
        stats = self.get_user_monthly_stats(user_id)
        if not stats:
            return 0.4  # 默认普通用户费用
        
        is_vip = stats.get('is_vip', False)
        monthly_count = stats.get('monthly_email_count', 0)
        
        if is_vip:
            if monthly_count < 100:
                return 0.0  # 会员用户前100条免费
            else:
                return 0.2  # 会员用户超出部分0.2元/条
        else:
            return 0.4  # 普通用户0.4元/条
    
    def add_recharge_record(self, user_id, recharge_type, amount, description=""):
        """添加充值记录"""
        query = """
        INSERT INTO recharge_records (user_id, type, amount, description)
        VALUES (%s, %s, %s, %s)
        """
        params = (user_id, recharge_type, amount, description)
        return self.execute_update(query, params)

    def add_billing_record(self, user_id, amount, type, description=""):
        """添加消费记录（通用方法）"""
        # 对于充值码类型，映射到balance类型
        if type == 'recharge_code':
            type = 'balance'
        return self.add_recharge_record(user_id, type, amount, description)

    def get_monthly_email_stats(self, user_id):
        """获取用户本月邮件发送统计"""
        from datetime import datetime

        # 获取本月第一天
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)

        query = """
        SELECT
            COUNT(*) as total_count,
            SUM(CASE WHEN cost = 0.4 THEN 1 ELSE 0 END) as normal_count,
            SUM(CASE WHEN cost = 0.0 AND is_vip_free = 1 THEN 1 ELSE 0 END) as vip_free_count,
            SUM(CASE WHEN cost = 0.2 THEN 1 ELSE 0 END) as vip_over_count
        FROM email_send_records
        WHERE user_id = %s AND sent_at >= %s
        """
        params = (user_id, month_start)
        result = self.execute_query(query, params)

        if result:
            stats = result[0]
            return {
                'total_count': stats['total_count'] or 0,
                'normal_count': stats['normal_count'] or 0,  # 普通用户¥0.4/条
                'vip_free_count': stats['vip_free_count'] or 0,  # VIP免费
                'vip_over_count': stats['vip_over_count'] or 0,  # VIP超额¥0.2/条
            }
        else:
            return {
                'total_count': 0,
                'normal_count': 0,
                'vip_free_count': 0,
                'vip_over_count': 0,
            }
    
    def add_email_billing(self, user_id, email_id, cost, user_type, monthly_count):
        """添加邮件计费记录"""
        query = """
        INSERT INTO email_billing (user_id, email_id, cost, user_type, monthly_count)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, email_id, cost, user_type, monthly_count)
        return self.execute_update(query, params)
    
    def get_user_recharge_history(self, user_id, limit=10):
        """获取用户充值历史"""
        query = """
        SELECT * FROM recharge_records 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        params = (user_id, limit)
        return self.execute_query(query, params)
    
    def get_user_billing_history(self, user_id, limit=10):
        """获取用户邮件计费历史"""
        query = """
        SELECT eb.*, e.subject 
        FROM email_billing eb 
        LEFT JOIN emails e ON eb.email_id = e.id
        WHERE eb.user_id = %s 
        ORDER BY eb.created_at DESC 
        LIMIT %s
        """
        params = (user_id, limit)
        return self.execute_query(query, params)
    
    # 待确认支付管理方法
    def create_pending_payment(self, record_data):
        """创建待确认支付记录"""
        query = """
        INSERT INTO pending_payments 
        (user_id, order_id, amount, payment_type, payment_method, status, 
         screenshot_path, screenshot_filename, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            record_data['user_id'],
            record_data['order_id'], 
            record_data['amount'],
            record_data['payment_type'],
            record_data['payment_method'],
            record_data['status'],
            record_data.get('screenshot_path'),
            record_data.get('screenshot_filename'),
            record_data['created_at'],
            record_data['updated_at']
        )
        result = self.execute_update(query, params)
        return result > 0
    
    def get_pending_payments(self, status=None, limit=50, offset=0):
        """获取待确认支付记录"""
        if status:
            query = """
            SELECT pp.*, u.username 
            FROM pending_payments pp 
            LEFT JOIN users u ON pp.user_id = u.id 
            WHERE pp.status = %s 
            ORDER BY pp.created_at DESC 
            LIMIT %s OFFSET %s
            """
            params = (status, limit, offset)
        else:
            query = """
            SELECT pp.*, u.username 
            FROM pending_payments pp 
            LEFT JOIN users u ON pp.user_id = u.id 
            ORDER BY pp.created_at DESC 
            LIMIT %s OFFSET %s
            """
            params = (limit, offset)
            
        return self.execute_query(query, params) or []
    
    def get_pending_payments_count(self, status=None):
        """获取待确认支付记录数量"""
        if status:
            query = "SELECT COUNT(*) as count FROM pending_payments WHERE status = %s"
            params = (status,)
        else:
            query = "SELECT COUNT(*) as count FROM pending_payments"
            params = ()
            
        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0
    
    def confirm_pending_payment(self, payment_id, admin_user_id, admin_note=""):
        """确认待支付订单"""
        try:
            # 获取支付记录
            query = "SELECT * FROM pending_payments WHERE id = %s AND status IN ('waiting_manual', 'waiting_auto')"
            payment = self.execute_query(query, (payment_id,))
            
            if not payment:
                return False, "订单不存在或已处理"
            
            payment = payment[0]
            
            # 处理充值
            if payment['payment_type'] == 'balance':
                # 余额充值
                success = self.update_user_balance(payment['user_id'], payment['amount'])
                if success:
                    description = f"余额充值¥{payment['amount']}（{payment['payment_method']}支付，管理员确认）"
                    if admin_note:
                        description += f" 备注：{admin_note}"
                    self.add_recharge_record(payment['user_id'], 'balance', payment['amount'], description)
                    
            elif payment['payment_type'] == 'vip':
                # 会员购买
                from datetime import datetime, timedelta
                expire_date = datetime.now() + timedelta(days=30)
                self.set_user_vip(payment['user_id'], expire_date)
                
                description = f"会员购买（1个月，{payment['payment_method']}支付，管理员确认）"
                if admin_note:
                    description += f" 备注：{admin_note}"
                self.add_recharge_record(payment['user_id'], 'vip', payment['amount'], description)
            
            # 更新支付记录状态
            from datetime import datetime
            update_query = """
            UPDATE pending_payments 
            SET status = 'confirmed', confirmed_at = %s, confirmed_by = %s, admin_note = %s, updated_at = %s
            WHERE id = %s
            """
            update_params = (datetime.now(), admin_user_id, admin_note, datetime.now(), payment_id)
            self.execute_update(update_query, update_params)
            
            return True, "确认成功"
            
        except Exception as e:
            print(f"❌ 确认支付失败: {e}")
            return False, f"确认失败: {str(e)}"
    
    def cancel_pending_payment(self, payment_id, admin_user_id, admin_note=""):
        """取消待支付订单"""
        try:
            from datetime import datetime
            update_query = """
            UPDATE pending_payments 
            SET status = 'cancelled', confirmed_at = %s, confirmed_by = %s, admin_note = %s, updated_at = %s
            WHERE id = %s AND status IN ('waiting_manual', 'waiting_auto')
            """
            update_params = (datetime.now(), admin_user_id, admin_note, datetime.now(), payment_id)
            result = self.execute_update(update_query, update_params)
            
            return result > 0, "取消成功" if result > 0 else "订单不存在或已处理"
            
        except Exception as e:
            print(f"❌ 取消支付失败: {e}")
            return False, f"取消失败: {str(e)}"

# 测试代码
if __name__ == "__main__":
    # 创建数据库管理器实例
    db_manager = DatabaseManager()
    
    # 连接数据库
    if db_manager.connect():
        # 测试查询
        users = db_manager.get_all_domains()
        if users:
            print("域名列表:")
            for user in users:
                print(f"  - {user['domain_name']}")
        else:
            print("未找到域名")
        
        # 断开连接
        db_manager.disconnect()
    else:
        print("无法连接到数据库")

# ========== 验证码发送限制管理方法 ==========
# 将这些方法添加到DatabaseManager类中

def add_verification_methods_to_db_manager():
    """将验证码限制方法添加到DatabaseManager类"""

    def check_verification_code_limit(self, user_id, email=None, daily_limit=2):
        """检查用户今日验证码发送次数是否超限"""
        try:
            from datetime import datetime, date
            today = date.today()

            # 构建查询条件
            if email:
                # 按邮箱地址限制
                query = """
                SELECT COUNT(*) as count FROM verification_code_logs
                WHERE email = %s AND DATE(sent_time) = %s
                """
                params = (email, today)
            else:
                # 按用户ID限制
                query = """
                SELECT COUNT(*) as count FROM verification_code_logs
                WHERE user_id = %s AND DATE(sent_time) = %s
                """
                params = (user_id, today)

            result = self.execute_query(query, params)
            if result:
                count = result[0]['count']
                return count < daily_limit, count
            return True, 0

        except Exception as e:
            print(f"⚠️ 检查验证码发送限制时出错: {e}")
            return True, 0  # 出错时允许发送

    def log_verification_code_sent(self, user_id, email, code_type, ip_address=None):
        """记录验证码发送日志"""
        try:
            from datetime import datetime

            query = """
            INSERT INTO verification_code_logs (user_id, email, code_type, sent_time, ip_address)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (user_id, email, code_type, datetime.now(), ip_address)
            result = self.execute_update(query, params)
            return result > 0

        except Exception as e:
            print(f"⚠️ 记录验证码发送日志时出错: {e}")
            return False

    def get_user_verification_code_stats(self, user_id):
        """获取用户验证码发送统计"""
        try:
            from datetime import datetime, date
            today = date.today()

            query = """
            SELECT
                COUNT(*) as today_count,
                MAX(sent_time) as last_sent_time
            FROM verification_code_logs
            WHERE user_id = %s AND DATE(sent_time) = %s
            """
            params = (user_id, today)
            result = self.execute_query(query, params)

            if result:
                return {
                    'today_count': result[0]['today_count'] or 0,
                    'last_sent_time': result[0]['last_sent_time'],
                    'remaining_count': max(0, 2 - (result[0]['today_count'] or 0))
                }
            return {'today_count': 0, 'last_sent_time': None, 'remaining_count': 2}

        except Exception as e:
            print(f"⚠️ 获取验证码发送统计时出错: {e}")
            return {'today_count': 0, 'last_sent_time': None, 'remaining_count': 2}