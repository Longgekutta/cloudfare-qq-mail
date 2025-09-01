# -*- coding: utf-8 -*-
"""
数据库设置脚本
用于连接到MySQL数据库并创建所需的表格
"""

import mysql.connector
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def setup_database():
    """设置数据库和表格"""
    connection = None
    cursor = None
    
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"数据库 '{DB_NAME}' 创建成功或已存在")
        
        # 使用数据库
        cursor.execute(f"USE {DB_NAME}")
        
        # 创建用户数据表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            is_vip BOOLEAN DEFAULT FALSE,
            balance DECIMAL(10, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("用户数据表创建成功")
        
        # 创建域名表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            id INT AUTO_INCREMENT PRIMARY KEY,
            domain_name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("域名表创建成功")
        
        # 创建邮件表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_email VARCHAR(100) NOT NULL,
            receiver_email VARCHAR(100) NOT NULL,
            subject VARCHAR(255),
            content TEXT,
            sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("邮件表创建成功")
        
        # 创建用户拥有的邮箱表
        cursor.execute("""
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
        )
        """)
        print("用户拥有的邮箱表创建成功")
        
        # 创建附件表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email_id INT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
        )
        """)
        print("附件表创建成功")
        
        # 插入示例数据
        # 插入示例域名
        cursor.execute("""
        INSERT IGNORE INTO domains (domain_name) VALUES 
        ('shiep.edu.kg'),
        ('example.com'),
        ('test.org')
        """)
        print("示例域名插入成功")
        
        # 插入示例用户
        cursor.execute("""
        INSERT IGNORE INTO users (username, password, is_vip, balance) VALUES 
        ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', TRUE, 100.00),
        ('user1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', FALSE, 50.00)
        """)
        print("示例用户插入成功")
        
        # 插入示例用户邮箱
        cursor.execute("""
        INSERT IGNORE INTO user_emails (user_id, email_address, domain_id) VALUES 
        (1, 'admin@shiep.edu.kg', 1),
        (2, 'user1@example.com', 2)
        """)
        print("示例用户邮箱插入成功")
        
        connection.commit()
        print("所有表格创建成功")
        
    except mysql.connector.Error as error:
        print(f"数据库连接或执行错误: {error}")
    except Exception as error:
        print(f"其他错误: {error}")
        
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == "__main__":
    setup_database()