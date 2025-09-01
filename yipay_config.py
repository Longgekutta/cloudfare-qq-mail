# -*- coding: utf-8 -*-
"""
易支付配置文件
"""

import os

# 易支付商户信息 - 优先使用环境变量
YIPAY_PID = os.getenv('YIPAY_PID', "6166")  # 商户PID
YIPAY_KEY = os.getenv('YIPAY_KEY', "deefc7cc0449be9cb621b7800f5e7f1c")  # 商户KEY，生产环境请使用环境变量
YIPAY_GATEWAY = os.getenv('YIPAY_GATEWAY', "https://pay.yzhifupay.com/")  # 支付网关

# 支付类型映射
PAYMENT_TYPES = {
    'alipay': 'alipay',     # 支付宝
    'wechat': 'wxpay',      # 微信支付
    'qq': 'qqpay'           # QQ支付
}

# 网站信息
SITE_NAME = "邮件系统"

# 支付回调地址（需要替换为你的实际域名）
DOMAIN = os.getenv('DOMAIN', "http://127.0.0.1:5000")  # 本地测试地址，生产环境需要替换为实际域名
RETURN_URL = f"{DOMAIN}/payment/return"      # 同步回调地址
NOTIFY_URL = f"{DOMAIN}/payment/notify"      # 异步通知地址

print("🔧 易支付配置已加载")
print(f"   商户PID: {YIPAY_PID}")
print(f"   支付网关: {YIPAY_GATEWAY}")
print(f"   回调域名: {DOMAIN}")












