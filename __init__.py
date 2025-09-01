# -*- coding: utf-8 -*-
# CloudFlare-QQ邮件处理系统
# 基于成功经验整合的邮件处理解决方案

"""
CloudFlare-QQ邮件处理系统

功能特性:
- QQ邮箱实时监控
- 自动邮件解析
- HTML内容重构
- 附件提取保存
- 完整的错误处理

使用示例:
    from cloudfare_qq_mail import AutoEmailProcessor
    
    processor = AutoEmailProcessor()
    processor.start_auto_processing()
"""

__version__ = "1.0.0"
__author__ = "justlovemaki"
__email__ = "YOUR_QQ_EMAIL@qq.com"

# 导入主要类
from .email_config import *
from .email_parser import EmailParser
from .qq_email_monitor import QQEmailMonitor
from .auto_email_processor import AutoEmailProcessor

# 导出的公共接口
__all__ = [
    'EmailParser',
    'QQEmailMonitor', 
    'AutoEmailProcessor',
    'QQ_EMAIL',
    'QQ_AUTH_CODE',
    'EMAIL_SAVE_DIR'
]

print("📧 CloudFlare-QQ邮件处理系统已加载")
print(f"版本: {__version__}")
print("基于成功经验整合，稳定可靠！")
