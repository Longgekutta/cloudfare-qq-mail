#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件系统启动程序
功能：统一启动整个邮件处理系统的所有组件
作者：系统管理员
版本：1.1
"""

import os
import sys
import time
import subprocess
import threading
import signal
from datetime import datetime

class 邮件系统启动器:
    def __init__(self):
        self.进程列表 = []
        self.运行状态 = {}
        self.启动时间 = datetime.now()
        
        # 系统组件配置
        self.系统组件 = {
            "邮件监控器": {
                "程序": "start_monitor.py",
                "描述": "QQ邮箱实时监控",
                "端口": None,
                "必需": True
            },
            "组件连接器": {
                "程序": "component_connector.py", 
                "描述": "邮件处理核心组件",
                "端口": None,
                "必需": True
            },
            "自动处理器": {
                "程序": "auto_email_processor.py",
                "描述": "邮件自动化处理",
                "端口": None,
                "必需": False
            },
            "Web应用": {
                "程序": "app.py",
                "描述": "用户界面Web服务",
                "端口": 5000,
                "必需": True
            }
        }
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.信号处理)
        signal.signal(signal.SIGTERM, self.信号处理)
    
    def 打印标题(self):
        """打印系统启动标题"""
        print("=" * 60)
        print("📧 邮件处理系统启动器")
        print("=" * 60)
        print(f"🕐 启动时间: {self.启动时间.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 工作目录: {os.getcwd()}")
        print("=" * 60)
    
    def 检查依赖(self):
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
    
    def 启动组件(self, 组件名, 配置):
        """启动单个系统组件"""
        try:
            print(f"🚀 启动 {组件名} ({配置['描述']})...")
            
            # 启动进程 - 修改为不阻塞输出
            进程 = subprocess.Popen(
                [sys.executable, 配置['程序']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            self.进程列表.append(进程)
            self.运行状态[组件名] = {
                "进程": 进程,
                "状态": "运行中",
                "启动时间": datetime.now()
            }
            
            print(f"✅ {组件名} 启动成功 (PID: {进程.pid})")
            
            # 等待一下确保进程稳定
            time.sleep(1)  # 减少等待时间

            # 检查进程是否还在运行（放宽检查条件）
            if 进程.poll() is None:
                print(f"🟢 {组件名} 运行正常")
                return True
            else:
                # 某些组件可能需要更长时间启动，不立即判定失败
                print(f"⚠️ {组件名} 启动中...")
                time.sleep(2)  # 再等待2秒
                if 进程.poll() is None:
                    print(f"🟢 {组件名} 启动成功")
                    return True
                else:
                    print(f"❌ {组件名} 启动失败")
                    return False
                
        except Exception as e:
            print(f"❌ 启动 {组件名} 时出错: {e}")
            return False
    
    def 检查端口(self, 端口):
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
    
    def 启动系统(self):
        """启动整个邮件系统"""
        print("🎯 开始启动邮件处理系统...")
        
        # 检查依赖
        if not self.检查依赖():
            print("❌ 系统依赖检查失败，无法启动")
            return False
        
        # 启动必需组件
        for 组件名, 配置 in self.系统组件.items():
            if 配置['必需']:
                # 检查端口
                if 配置['端口'] and not self.检查端口(配置['端口']):
                    print(f"⚠️ 端口 {配置['端口']} 已被占用，跳过 {组件名}")
                    continue
                
                if not self.启动组件(组件名, 配置):
                    if 配置['必需']:
                        print(f"❌ 必需组件 {组件名} 启动失败，系统无法运行")
                        self.停止系统()
                        return False
        
        # 启动可选组件
        for 组件名, 配置 in self.系统组件.items():
            if not 配置['必需']:
                if 配置['端口'] and not self.检查端口(配置['端口']):
                    print(f"⚠️ 端口 {配置['端口']} 已被占用，跳过 {组件名}")
                    continue
                
                self.启动组件(组件名, 配置)
        
        print("🎉 邮件系统启动完成！")
        return True
    
    def 监控系统(self):
        """监控系统运行状态"""
        print("\n📊 系统运行状态监控")
        print("=" * 60)
        
        while True:
            try:
                # 清屏
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("=" * 60)
                print("📊 邮件系统运行状态")
                print("=" * 60)
                print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️ 运行时长: {datetime.now() - self.启动时间}")
                print("=" * 60)
                
                运行中组件 = 0
                for 组件名, 状态 in self.运行状态.items():
                    进程 = 状态['进程']
                    if 进程.poll() is None:
                        print(f"🟢 {组件名}: 运行中 (PID: {进程.pid})")
                        运行中组件 += 1
                    else:
                        print(f"🔴 {组件名}: 已停止")
                
                print("=" * 60)
                print(f"📈 运行状态: {运行中组件}/{len(self.运行状态)} 个组件运行中")
                print("💡 按 Ctrl+C 停止系统")
                print("=" * 60)
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"监控出错: {e}")
                time.sleep(5)
    
    def 停止系统(self):
        """停止整个邮件系统"""
        print("\n🛑 正在停止邮件系统...")
        
        for 组件名, 状态 in self.运行状态.items():
            try:
                进程 = 状态['进程']
                if 进程.poll() is None:
                    print(f"🛑 停止 {组件名}...")
                    进程.terminate()
                    
                    # 等待进程结束
                    try:
                        进程.wait(timeout=10)
                        print(f"✅ {组件名} 已停止")
                    except subprocess.TimeoutExpired:
                        print(f"⚠️ {组件名} 强制终止")
                        进程.kill()
                        
            except Exception as e:
                print(f"❌ 停止 {组件名} 时出错: {e}")
        
        print("🎉 邮件系统已完全停止")
    
    def 信号处理(self, signum, frame):
        """处理系统信号"""
        print(f"\n📡 收到信号 {signum}，正在停止系统...")
        self.停止系统()
        sys.exit(0)
    
    def 显示帮助(self):
        """显示帮助信息"""
        print("📖 邮件系统启动器使用说明")
        print("=" * 60)
        print("功能：统一启动邮件处理系统的所有组件")
        print("")
        print("系统组件：")
        for 组件名, 配置 in self.系统组件.items():
            必需标记 = "必需" if 配置['必需'] else "可选"
            端口信息 = f"端口:{配置['端口']}" if 配置['端口'] else "无端口"
            print(f"  • {组件名}: {配置['描述']} ({必需标记}, {端口信息})")
        print("")
        print("使用方法：")
        print("  python 启动邮件系统.py")
        print("")
        print("控制：")
        print("  Ctrl+C: 停止系统")
        print("=" * 60)

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        启动器 = 邮件系统启动器()
        启动器.显示帮助()
        return
    
    # 创建启动器
    启动器 = 邮件系统启动器()
    
    try:
        # 显示标题
        启动器.打印标题()
        
        # 启动系统
        if 启动器.启动系统():
            # 开始监控
            启动器.监控系统()
        else:
            print("❌ 系统启动失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n📡 用户中断，正在停止系统...")
        启动器.停止系统()
    except Exception as e:
        print(f"❌ 系统运行出错: {e}")
        启动器.停止系统()
        sys.exit(1)

if __name__ == "__main__":
    main()
