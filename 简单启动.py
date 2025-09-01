#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件系统简单启动程序
功能：快速启动邮件处理系统的主要组件
作者：系统管理员
版本：1.0
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def 打印标题():
    """打印系统启动标题"""
    print("=" * 60)
    print("📧 邮件处理系统 - 简单启动器")
    print("=" * 60)
    print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 工作目录: {os.getcwd()}")
    print("=" * 60)

def 检查依赖():
    """检查系统依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本过低，需要3.7或更高版本")
        return False
    
    # 检查必需文件
    必需文件 = [
        "email_config.py",
        "database/db_manager.py", 
        "frontend/templates/index.html"
    ]
    
    for 文件 in 必需文件:
        if not os.path.exists(文件):
            print(f"❌ 缺少必需文件: {文件}")
            return False
    
    print("✅ 系统依赖检查完成")
    return True

def 启动组件(组件名, 程序文件):
    """启动单个组件"""
    try:
        print(f"🚀 启动 {组件名}...")
        
        # 在Windows上使用start命令启动新窗口
        if os.name == 'nt':
            cmd = f'start "邮件系统 - {组件名}" python "{程序文件}"'
            subprocess.run(cmd, shell=True)
        else:
            # 在Linux/Mac上使用后台运行
            cmd = f'python3 "{程序文件}" &'
            subprocess.run(cmd, shell=True)
        
        print(f"✅ {组件名} 启动成功")
        return True
        
    except Exception as e:
        print(f"❌ 启动 {组件名} 时出错: {e}")
        return False

def 检查端口(端口):
    """检查端口是否被占用"""
    if 端口 is None:
        return True
        
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 端口))
        sock.close()
        return result != 0
    except:
        return True

def 启动系统():
    """启动邮件系统"""
    print("🎯 开始启动邮件处理系统...")
    
    # 检查依赖
    if not 检查依赖():
        print("❌ 系统依赖检查失败，无法启动")
        return False
    
    # 系统组件列表
    # 注意：只启动组件连接器，避免重复监控邮件
    组件列表 = [
        ("组件连接器", "component_connector.py", None),
        ("Web应用", "app.py", 5000)
    ]
    
    # 启动组件
    for 组件名, 程序文件, 端口 in 组件列表:
        # 检查端口
        if 端口 and not 检查端口(端口):
            print(f"⚠️ 端口 {端口} 已被占用，跳过 {组件名}")
            continue
        
        if not 启动组件(组件名, 程序文件):
            print(f"❌ {组件名} 启动失败")
            if 组件名 in ["组件连接器", "Web应用"]:
                print("❌ 必需组件启动失败，系统无法正常运行")
                return False
    
    print("🎉 邮件系统启动完成！")
    print("=" * 60)
    print("📋 启动的组件：")
    print("  • 组件连接器 - 统一邮件监控与处理核心")
    print("  • Web应用 - 用户界面Web服务 (端口5000)")
    print("=" * 60)
    print("🌐 访问地址: http://localhost:5000")
    print("🔐 管理员账号: admin / admin123")
    print("=" * 60)
    print("💡 提示：")
    print("  • 每个组件都在独立的窗口中运行")
    print("  • 关闭对应窗口即可停止该组件")
    print("  • 如需停止所有组件，请关闭所有相关窗口")
    print("=" * 60)
    
    return True

def 显示帮助():
    """显示帮助信息"""
    print("📖 邮件系统简单启动器使用说明")
    print("=" * 60)
    print("功能：快速启动邮件处理系统的主要组件")
    print("")
    print("启动的组件：")
    print("  • 邮件监控器: QQ邮箱实时监控")
    print("  • 组件连接器: 邮件处理核心组件")
    print("  • Web应用: 用户界面Web服务 (端口5000)")
    print("  • 自动处理器: 邮件自动化处理")
    print("")
    print("使用方法：")
    print("  python 简单启动.py")
    print("")
    print("特点：")
    print("  • 每个组件在独立窗口中运行")
    print("  • 无需复杂的进程管理")
    print("  • 简单易用，适合日常使用")
    print("=" * 60)

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        显示帮助()
        return
    
    try:
        # 显示标题
        打印标题()
        
        # 启动系统
        if 启动系统():
            print("\n🎉 系统启动成功！")
            print("请查看各个组件的运行窗口，确认系统正常运行。")
        else:
            print("❌ 系统启动失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n📡 用户中断启动过程")
    except Exception as e:
        print(f"❌ 系统启动出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
