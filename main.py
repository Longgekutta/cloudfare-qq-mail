# -*- coding: utf-8 -*-
# 邮件处理系统启动脚本
# 基于成功经验的简单启动方式

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from auto_email_processor import AutoEmailProcessor

def main():
    """主启动函数"""
    print("🚀 邮件处理系统启动")
    print("="*50)
    print("基于QQ邮箱的成功处理方案")
    print("功能: 监控 → 下载 → 解析 → HTML生成")
    print("="*50)
    
    try:
        # 创建处理器
        processor = AutoEmailProcessor()
        
        # 测试连接
        print("\n🧪 测试QQ邮箱连接...")
        mail = processor.monitor.connect_to_qq_imap()
        
        if mail:
            print("✅ 连接测试成功！")
            mail.close()
            mail.logout()
            
            # 执行一次检查
            print("\n📬 执行一次邮件检查...")
            result = processor.enhanced_monitor_once()
            
            if result is not False:
                print("\n✅ 系统测试成功！")
                
                if result:
                    print(f"📬 处理了 {len(result)} 封新邮件")
                    
                    # 显示处理结果
                    for i, email_result in enumerate(result, 1):
                        email_data = email_result['email_data']
                        html_path = email_result['html_path']
                        
                        print(f"\n📧 邮件 {i}:")
                        print(f"   发件人: {email_data['info']['from']}")
                        print(f"   主题: {email_data['info']['subject']}")
                        print(f"   HTML: {html_path}")
                        
                else:
                    print("📭 当前无新邮件")
                
                print("\n" + "="*50)
                print("选择运行模式:")
                print("1. 仅执行一次检查 (已完成)")
                print("2. 启动连续监控模式")
                print("3. 退出")
                
                while True:
                    choice = input("\n请选择 (1-3): ").strip()
                    
                    if choice == "1":
                        print("✅ 单次检查已完成，程序结束")
                        break
                    elif choice == "2":
                        print("\n🔄 启动连续监控模式...")
                        print("按 Ctrl+C 停止监控")
                        processor.start_auto_processing()
                        break
                    elif choice == "3":
                        print("👋 程序结束")
                        break
                    else:
                        print("❌ 无效选择，请输入 1-3")
            else:
                print("❌ 系统测试失败")
        else:
            print("❌ 连接测试失败")
            print("\n💡 解决建议:")
            print("1. 检查QQ邮箱IMAP服务是否开启")
            print("2. 检查授权码是否正确")
            print("3. 检查网络连接")
            
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 程序结束")

if __name__ == "__main__":
    main()
