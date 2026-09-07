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
    # 由于项目主要作为独立脚本运行，推荐直接将项目根目录加入 sys.path
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from auto_email_processor import AutoEmailProcessor

    processor = AutoEmailProcessor()
    processor.start_auto_processing()
"""

__version__ = "1.0.0"
__author__ = "justlovemaki"
__email__ = ""

import logging

logger = logging.getLogger(__name__)

# 兼容作为包导入（相对导入）和直接运行脚本（绝对导入）
try:
    from .email_config import QQ_EMAIL, QQ_AUTH_CODE, EMAIL_SAVE_DIR
    from .email_parser import EmailParser
    from .qq_email_monitor import QQEmailMonitor
    from .auto_email_processor import AutoEmailProcessor
except ImportError:
    from email_config import QQ_EMAIL, QQ_AUTH_CODE, EMAIL_SAVE_DIR
    from email_parser import EmailParser
    from qq_email_monitor import QQEmailMonitor
    from auto_email_processor import AutoEmailProcessor

# 导出的公共接口
__all__ = [
    'EmailParser',
    'QQEmailMonitor',
    'AutoEmailProcessor',
    'QQ_EMAIL',
    'QQ_AUTH_CODE',
    'EMAIL_SAVE_DIR'
]

logger.debug("📧 CloudFlare-QQ邮件处理系统已加载 (v%s) - 基于成功经验整合，稳定可靠！", __version__)
