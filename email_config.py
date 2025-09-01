# -*- coding: utf-8 -*-
# QQ邮箱配置文件
# 基于成功的配置经验整合

# 数据库配置 - 支持环境变量覆盖
import os

# QQ邮箱配置 - 优先使用环境变量
QQ_EMAIL = os.getenv('QQ_EMAIL', "2846117874@qq.com")
QQ_AUTH_CODE = os.getenv('QQ_AUTH_CODE', "ajqnryrvvjmsdcgi")  # 生产环境请使用环境变量

# IMAP服务器配置
IMAP_SERVER = "imap.qq.com"
IMAP_PORT = 993
USE_SSL = True

# 邮件处理配置
EMAIL_SAVE_DIR = "./received_emails"
CHECK_INTERVAL = 6  # 检查间隔（秒）- 改为6秒快速监控

# 邮件过滤配置
TARGET_DOMAIN = os.getenv('TARGET_DOMAIN', "shiep.edu.kg")  # 只处理这个域名的邮件
PROCESS_HISTORICAL = False  # 不处理历史邮件，只处理新邮件

# Cloudflare配置（预留）
CLOUDFLARE_DOMAIN = "shiep.edu.kg"
CLOUDFLARE_WORKER_NAME = "longgekutta"

# 文件路径配置
HTML_OUTPUT_DIR = "./html_output"
ATTACHMENT_DIR = "./attachments"

# 调试配置
DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
SAVE_RAW_EMAIL = True

print("邮件处理配置已加载")
print(f"监控邮箱: {QQ_EMAIL}")
print(f"保存目录: {EMAIL_SAVE_DIR}")

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '518107qW')  # 生产环境请使用环境变量
DB_NAME = os.getenv('DB_NAME', 'cloudfare_qq_mail')

print(f"数据库名称: {DB_NAME}")
