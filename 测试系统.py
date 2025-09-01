#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件系统测试程序
功能：测试系统各个组件是否正常工作
作者：系统管理员
版本：1.0
"""

import os
import sys
import time
import subprocess
import requests
from datetime import datetime

def 打印标题():
    """打印测试标题"""
    print("=" * 60)
    print("🧪 邮件处理系统 - 功能测试")
    print("=" * 60)
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 工作目录: {os.getcwd()}")
    print("=" * 60)

def 测试数据库():
    """测试数据库连接"""
    try:
        print("🗄️ 测试数据库连接...")
        
        # 导入数据库管理器
        sys.path.append('database')
        from db_manager import DatabaseManager
        
        # 创建数据库连接
        db = DatabaseManager()
        db.connect()
        
        # 测试查询
        result = db.execute_query("SELECT COUNT(*) as count FROM users")
        if result:
            print(f"✅ 数据库连接成功，用户数量: {result[0]['count']}")
            db.close()
            return True
        else:
            print("❌ 数据库查询失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def 测试Web服务(端口=5000):
    """测试Web服务"""
    try:
        print(f"🌐 测试Web服务 (端口 {端口})...")
        
        # 尝试连接Web服务
        response = requests.get(f"http://localhost:{端口}", timeout=10)
        
        if response.status_code == 200:
            print("✅ Web服务正常运行")
            return True
        else:
            print(f"❌ Web服务响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Web服务无法连接")
        return False
    except requests.exceptions.Timeout:
        print("❌ Web服务连接超时")
        return False
    except Exception as e:
        print(f"❌ Web服务测试失败: {e}")
        return False

def 测试邮件配置():
    """测试邮件配置"""
    try:
        print("📧 测试邮件配置...")
        
        # 导入邮件配置
        from email_config import QQ_EMAIL, QQ_AUTH_CODE
        
        if QQ_EMAIL and QQ_AUTH_CODE:
            print(f"✅ 邮件配置正常: {QQ_EMAIL}")
            return True
        else:
            print("❌ 邮件配置不完整")
            return False
            
    except Exception as e:
        print(f"❌ 邮件配置测试失败: {e}")
        return False

def 测试文件完整性():
    """测试必需文件是否存在"""
    try:
        print("📁 测试文件完整性...")
        
        必需文件 = [
            "email_config.py",
            "database/db_manager.py",
            "database/setup_database.py",
            "frontend/templates/index.html",
            "start_monitor.py",
            "component_connector.py",
            "app.py"
        ]
        
        缺失文件 = []
        for 文件 in 必需文件:
            if not os.path.exists(文件):
                缺失文件.append(文件)
        
        if not 缺失文件:
            print("✅ 所有必需文件都存在")
            return True
        else:
            print(f"❌ 缺失文件: {', '.join(缺失文件)}")
            return False
            
    except Exception as e:
        print(f"❌ 文件完整性测试失败: {e}")
        return False

def 测试端口占用(端口=5000):
    """测试端口是否被占用"""
    try:
        print(f"🔌 测试端口 {端口} 占用情况...")
        
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 端口))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口 {端口} 正在使用中")
            return True
        else:
            print(f"⚠️ 端口 {端口} 未被占用")
            return False
            
    except Exception as e:
        print(f"❌ 端口测试失败: {e}")
        return False

def 运行完整测试():
    """运行完整的系统测试"""
    print("🎯 开始系统功能测试...")
    
    测试结果 = {}
    
    # 测试文件完整性
    测试结果['文件完整性'] = 测试文件完整性()
    
    # 测试邮件配置
    测试结果['邮件配置'] = 测试邮件配置()
    
    # 测试数据库
    测试结果['数据库'] = 测试数据库()
    
    # 测试端口占用
    测试结果['端口占用'] = 测试端口占用()
    
    # 测试Web服务
    测试结果['Web服务'] = 测试Web服务()
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    通过测试 = 0
    总测试数 = len(测试结果)
    
    for 测试名, 结果 in 测试结果.items():
        状态 = "✅ 通过" if 结果 else "❌ 失败"
        print(f"  {测试名}: {状态}")
        if 结果:
            通过测试 += 1
    
    print("=" * 60)
    print(f"📈 测试通过率: {通过测试}/{总测试数} ({通过测试/总测试数*100:.1f}%)")
    
    if 通过测试 == 总测试数:
        print("🎉 所有测试通过！系统可以正常启动。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查系统配置。")
        return False

def 显示帮助():
    """显示帮助信息"""
    print("📖 邮件系统测试程序使用说明")
    print("=" * 60)
    print("功能：测试邮件处理系统的各个组件")
    print("")
    print("测试项目：")
    print("  • 文件完整性 - 检查必需文件是否存在")
    print("  • 邮件配置 - 验证邮件配置是否正确")
    print("  • 数据库 - 测试数据库连接")
    print("  • 端口占用 - 检查Web服务端口")
    print("  • Web服务 - 测试Web服务是否运行")
    print("")
    print("使用方法：")
    print("  python 测试系统.py")
    print("")
    print("建议：")
    print("  • 在启动系统前运行此测试")
    print("  • 如果测试失败，请先解决问题再启动系统")
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
        
        # 运行测试
        if 运行完整测试():
            print("\n🎉 系统测试完成，可以正常启动！")
            print("建议使用 'python 完整启动.py' 启动系统")
        else:
            print("\n❌ 系统测试失败，请检查配置后重试")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n📡 用户中断测试")
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

