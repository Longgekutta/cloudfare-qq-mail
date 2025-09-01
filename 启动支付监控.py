#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成启动脚本 - 邮件系统 + 支付监控
"""

import threading
import time
import subprocess
import sys
import os

# 添加项目目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from payment_monitor import PaymentMonitor

def start_flask_app():
    """启动Flask Web应用"""
    print("🚀 启动Flask Web应用...")
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("📧 Flask应用已停止")
    except Exception as e:
        print(f"❌ Flask应用启动失败: {e}")

def start_email_monitor():
    """启动邮件监控"""
    print("📧 启动邮件监控系统...")
    try:
        subprocess.run([sys.executable, 'realtime_monitor.py'], check=True)
    except KeyboardInterrupt:
        print("📧 邮件监控已停止")
    except Exception as e:
        print(f"❌ 邮件监控启动失败: {e}")

def start_payment_monitor():
    """启动支付监控"""
    print("💰 启动支付监控系统...")
    
    # 配置支付监控邮箱（用于接收支付宝通知）
    # 建议单独申请一个QQ邮箱用于接收支付宝通知
    payment_email_config = {
        'imap_server': 'imap.qq.com',
        'imap_port': 993,
        'username': '您的支付通知邮箱@qq.com',  # 请修改
        'password': '您的授权码'  # 请修改为实际授权码
    }
    
    try:
        monitor = PaymentMonitor(payment_email_config)
        monitor.start_monitor()
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("💰 支付监控已停止")
        if 'monitor' in locals():
            monitor.stop_monitor()
    except Exception as e:
        print(f"❌ 支付监控启动失败: {e}")

def main():
    """主函数"""
    print("="*60)
    print("🚀 启动完整邮件系统（包含支付监控）")
    print("="*60)
    
    # 检查配置
    config_ok = check_configuration()
    if not config_ok:
        print("❌ 配置检查失败，请先完成配置")
        return
    
    try:
        # 创建并启动线程
        flask_thread = threading.Thread(target=start_flask_app, daemon=True)
        email_thread = threading.Thread(target=start_email_monitor, daemon=True)
        payment_thread = threading.Thread(target=start_payment_monitor, daemon=True)
        
        # 启动所有服务
        flask_thread.start()
        time.sleep(2)  # 等待Flask启动
        
        email_thread.start()
        time.sleep(2)  # 等待邮件监控启动
        
        payment_thread.start()
        time.sleep(2)  # 等待支付监控启动
        
        print("\n" + "="*60)
        print("✅ 系统启动完成！")
        print("📧 Web界面: http://127.0.0.1:5000")
        print("📧 邮件监控: 已启动")
        print("💰 支付监控: 已启动")
        print("="*60)
        print("\n⚠️  使用说明：")
        print("1. 在支付宝中设置收款到账通知发送到您配置的邮箱")
        print("2. 用户付款时请在备注中写明订单号或用户信息")
        print("3. 系统会自动监控邮箱并处理充值")
        print("4. 按 Ctrl+C 停止所有服务")
        print("="*60)
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 正在停止所有服务...")
        print("✅ 系统已安全退出")
    except Exception as e:
        print(f"❌ 系统运行出错: {e}")

def check_configuration():
    """检查配置"""
    print("🔍 检查系统配置...")
    
    # 检查必要文件
    required_files = [
        'app.py',
        'payment_monitor.py',
        'realtime_monitor.py',
        'email_config.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return False
            
    # 检查二维码文件 - 商户收款码
    qr_files = ['wx-bissness-pay.png', 'zfb-bissness-pay.jpg']
    for qr_file in qr_files:
        if not os.path.exists(qr_file):
            print(f"❌ 缺少商户收款码文件: {qr_file}")
            return False
            
    print("✅ 基本配置检查通过")
    
    # 提醒用户配置支付监控邮箱
    print("\n⚠️  请确保已配置支付监控邮箱:")
    print("1. 在 payment_monitor.py 中设置正确的邮箱账号和授权码")
    print("2. 在支付宝中设置收款通知发送到该邮箱")
    print("3. 确保邮箱可以正常接收支付宝通知邮件")
    
    confirm = input("\n✅ 是否已完成支付邮箱配置？(y/N): ")
    return confirm.lower() in ['y', 'yes']

if __name__ == '__main__':
    main()
