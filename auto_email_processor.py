# -*- coding: utf-8 -*-
# 完整的邮件自动化处理系统 - 基于成功经验整合
# 集成：监控 → 下载 → 转换 → 解析 → 存储 → 显示
# 作者: justlovemaki
# 日期: 2025年8月22日

import os
import time
from datetime import datetime
from qq_email_monitor import QQEmailMonitor
from email_parser import EmailParser
from email_config import QQ_EMAIL, QQ_AUTH_CODE, EMAIL_SAVE_DIR, CHECK_INTERVAL
from database.db_manager import DatabaseManager

class AutoEmailProcessor:
    """
    完整的邮件自动化处理系统 - 已验证可用版本
    实现：QQ邮箱监控 → .eml转换 → 自动解析 → HTML生成 → 文件保存
    """
    
    def __init__(self, qq_email=None, qq_auth_code=None):
        self.qq_email = qq_email or QQ_EMAIL
        self.qq_auth_code = qq_auth_code or QQ_AUTH_CODE
        
        # 创建监控器
        self.monitor = QQEmailMonitor(self.qq_email, self.qq_auth_code, EMAIL_SAVE_DIR)
        
        # 创建解析器
        self.parser = EmailParser()
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager()
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'successful_parsed': 0,
            'failed_parsed': 0,
            'start_time': datetime.now()
        }
        
        print(f"🚀 邮件自动化处理系统已启动")
        print(f"📧 监控邮箱: {self.qq_email}")
        print(f"💾 邮件保存: {EMAIL_SAVE_DIR}")
        print(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
    
    def process_single_email(self, email_file_info):
        """处理单封邮件的完整流程"""
        try:
            print(f"\n🔄 开始处理邮件: {email_file_info['filename']}")
            
            # 1. 使用成功的解析器解析.eml文件
            email_data = self.parser.load_eml_file(email_file_info['filepath'])
            
            if not email_data:
                print(f"❌ 邮件解析失败")
                self.stats['failed_parsed'] += 1
                return False
            
            # 2. 提取关键信息
            info = email_data['info']
            content = email_data['content']
            
            print(f"📧 邮件信息:")
            print(f"   发件人: {info['from']}")
            print(f"   主题: {info['subject']}")
            print(f"   日期: {info['date']}")
            print(f"   附件数: {len(content['attachments'])}")
            
            # 3. 生成HTML显示文件
            html_content = self.parser.reconstruct_html_for_display(content)
            html_path = email_file_info['filepath'].replace('.eml', '_display.html')
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"🌐 HTML显示文件已生成: {html_path}")
            
            # 4. 保存邮件数据到数据库
            email_id = None
            try:
                # 连接数据库
                if self.db_manager.connect():
                    # 提取邮件信息
                    sender_email = info.get('from', '')
                    receiver_email = info.get('to', '')
                    subject = info.get('subject', '')
                    sent_time_raw = info.get('date', '')
                    
                    # 解析和格式化日期时间
                    sent_time = datetime.now()  # 默认值
                    if sent_time_raw:
                        try:
                            import email.utils
                            # 解析邮件日期
                            parsed_date = email.utils.parsedate_to_datetime(sent_time_raw)
                            # 转换为MySQL兼容的格式（去掉时区信息）
                            if parsed_date.tzinfo is not None:
                                sent_time = parsed_date.replace(tzinfo=None)
                            else:
                                sent_time = parsed_date
                        except Exception as date_error:
                            print(f"⚠️ 日期解析失败，使用当前时间: {date_error}")
                            sent_time = datetime.now()
                    
                    # 提取邮件内容
                    email_content = content.get('html', content.get('text', ''))
                    
                    # 保存邮件到数据库
                    email_id = self.db_manager.save_email(sender_email, receiver_email, subject, email_content, sent_time)
                    if email_id > 0:
                        print("✅ 邮件数据已保存到数据库")
                    else:
                        print("❌ 保存邮件数据到数据库失败")
                    
                    # 断开数据库连接
                    self.db_manager.disconnect()
                else:
                    print("❌ 数据库连接失败")
            except Exception as e:
                print(f"❌ 保存邮件数据到数据库时出错: {e}")
            
            # 5. 保存附件（如果有）
            if content['attachments']:
                attachment_dir = os.path.join(EMAIL_SAVE_DIR, 'attachments')
                os.makedirs(attachment_dir, exist_ok=True)
                
                for attachment in content['attachments']:
                    att_path = os.path.join(attachment_dir, attachment['filename'])
                    with open(att_path, 'wb') as f:
                        import base64
                        f.write(base64.b64decode(attachment['data']))
                    print(f"📎 附件已保存: {attachment['filename']}")
                    
                    # 将附件信息存储到数据库
                    if email_id and email_id > 0:
                        try:
                            if self.db_manager.connect():
                                result = self.db_manager.create_attachment(
                                    email_id=email_id,
                                    filename=attachment['filename'],
                                    file_path=att_path,
                                    file_size=len(base64.b64decode(attachment['data']))
                                )
                                if result > 0:
                                    print(f"✅ 附件信息已保存到数据库: {attachment['filename']}")
                                else:
                                    print(f"❌ 保存附件信息到数据库失败: {attachment['filename']}")
                                self.db_manager.disconnect()
                            else:
                                print("❌ 数据库连接失败，无法保存附件信息")
                        except Exception as e:
                            print(f"❌ 保存附件信息到数据库时出错: {e}")
            
            # 5. 这里可以添加其他处理逻辑
            # - 数据库存储
            # - 自动回复
            # - 转发处理
            # - API调用等
            
            self.stats['successful_parsed'] += 1
            self.stats['total_processed'] += 1
            
            print(f"🎉 邮件处理完成!")
            
            return {
                'email_data': email_data,
                'html_path': html_path,
                'processed_time': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ 处理邮件时出错: {e}")
            self.stats['failed_parsed'] += 1
            self.stats['total_processed'] += 1
            return False
    
    def enhanced_monitor_once(self):
        """增强版的单次监控"""
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 检查新邮件...")
        
        # 连接QQ邮箱
        mail = self.monitor.connect_to_qq_imap()
        if not mail:
            return False
        
        try:
            # 获取新邮件
            new_emails = self.monitor.get_new_emails(mail)
            
            if new_emails:
                print(f"📬 发现 {len(new_emails)} 封新邮件，开始自动化处理...")
                
                processed_results = []
                
                for email_data in new_emails:
                    # 1. 保存为.eml文件
                    file_info = self.monitor.save_email_as_eml(email_data)
                    
                    if file_info:
                        # 2. 完整处理流程
                        result = self.process_single_email(file_info)
                        
                        if result:
                            processed_results.append(result)
                            print(f"✅ {file_info['filename']} 处理完成")
                        else:
                            print(f"❌ {file_info['filename']} 处理失败")
                
                print(f"📊 本次处理结果: {len(processed_results)}/{len(new_emails)} 封邮件成功")
                return processed_results
            
            else:
                print("📭 暂无新邮件")
                return []
            
        except Exception as e:
            print(f"❌ 监控过程出错: {e}")
            return False
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
    
    def start_auto_processing(self, check_interval=None):
        """启动自动化处理"""
        interval = check_interval or CHECK_INTERVAL
        print(f"🔄 启动邮件自动化处理 (每{interval}秒检查一次)")
        
        try:
            while True:
                # 执行一次完整检查和处理
                result = self.enhanced_monitor_once()
                
                # 打印统计信息
                if self.stats['total_processed'] > 0:
                    self.print_stats()
                
                # 等待下次检查
                print(f"⏸️ 等待{interval}秒后进行下次检查...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 用户中断自动化处理")
            self.print_final_stats()
        except Exception as e:
            print(f"❌ 自动化处理过程出错: {e}")
            self.print_final_stats()
    
    def print_stats(self):
        """打印统计信息"""
        total = self.stats['total_processed']
        success = self.stats['successful_parsed']
        failed = self.stats['failed_parsed']
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"\n📊 处理统计:")
        print(f"   总处理: {total} 封")
        print(f"   成功: {success} 封")
        print(f"   失败: {failed} 封")
        print(f"   成功率: {success_rate:.1f}%")
    
    def print_final_stats(self):
        """打印最终统计"""
        print("\n" + "="*50)
        print("📊 最终统计报告")
        print("="*50)
        
        start_time = self.stats['start_time']
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"⏰ 运行时间: {duration}")
        print(f"📧 监控邮箱: {self.qq_email}")
        self.print_stats()
        print("="*50)
        print("✅ 邮件自动化处理已结束")

# 使用示例
def main():
    """主函数 - 启动完整的自动化邮件处理"""
    print("🚀 启动完整邮件自动化处理系统")
    print("="*50)
    
    try:
        # 创建自动化处理器
        processor = AutoEmailProcessor()
        
        # 先测试一次连接
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
                print("✅ 系统测试成功！")
                
                # 询问是否启动连续监控
                print("\n" + "="*50)
                print("系统已准备就绪！")
                print("选择运行模式:")
                print("1. 仅执行一次检查 (已完成)")
                print("2. 启动连续监控模式")
                print("3. 退出")
                
                choice = input("请选择 (1-3): ").strip()
                
                if choice == "2":
                    print("\n🔄 启动连续监控模式...")
                    processor.start_auto_processing()
                else:
                    print("👋 程序结束")
            else:
                print("❌ 系统测试失败")
        else:
            print("❌ 连接测试失败，请检查QQ邮箱配置")
            
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()

def quick_test():
    """快速测试 - 只检查一次"""
    print("🧪 快速测试模式")
    
    processor = AutoEmailProcessor()
    result = processor.enhanced_monitor_once()
    
    if result is not False:
        print("✅ 快速测试成功！")
        if result:
            print(f"📬 处理了 {len(result)} 封新邮件")
        else:
            print("📭 当前无新邮件")
    else:
        print("❌ 快速测试失败")

if __name__ == "__main__":
    # 可以选择运行模式
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        main()
