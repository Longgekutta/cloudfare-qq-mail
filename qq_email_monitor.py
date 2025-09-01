# -*- coding: utf-8 -*-
# QQ邮箱自动监控系统 - 基于成功经验整合
# 实时检测新邮件并自动转换为.eml文件
# 作者: justlovemaki
# 日期: 2025年8月22日

import imaplib
import email
import os
import time
import threading
import ssl
from datetime import datetime
from email_parser import EmailParser
from email_config import QQ_EMAIL, QQ_AUTH_CODE, EMAIL_SAVE_DIR

class QQEmailMonitor:
    """
    QQ邮箱实时监控系统 - 已验证可用版本
    自动检测新邮件并转换为.eml格式
    """
    
    def __init__(self, email_account=None, password=None, save_directory=None):
        self.email_account = email_account or QQ_EMAIL
        self.password = password or QQ_AUTH_CODE
        self.save_directory = save_directory or EMAIL_SAVE_DIR
        self.imap_server = "imap.qq.com"
        self.imap_port = 993
        self.is_monitoring = False
        self.last_check_time = datetime.now()
        self.system_start_time = datetime.now()  # 记录系统启动时间
        self.processed_emails = set()  # 记录已处理的邮件ID
        
        # 创建保存目录
        os.makedirs(self.save_directory, exist_ok=True)
        
        print(f"📧 初始化QQ邮箱监控: {self.email_account}")
        print(f"💾 邮件保存目录: {self.save_directory}")
        print(f"🕐 系统启动时间: {self.system_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def connect_to_qq_imap(self):
        """连接到QQ邮箱IMAP服务器"""
        try:
            print("🔗 连接QQ邮箱IMAP服务器...")
            
            # 创建SSL上下文以解决协议兼容性问题
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 连接IMAP服务器
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=ssl_context)
            
            # 登录QQ邮箱
            mail.login(self.email_account, self.password)
            
            # 选择收件箱
            mail.select('INBOX')
            
            print("✅ QQ邮箱连接成功！")
            return mail
            
        except Exception as e:
            print(f"❌ QQ邮箱连接失败: {e}")
            return None
    
    def get_new_emails(self, mail):
        """获取新邮件 - 只处理系统启动后收到的邮件"""
        try:
            # 搜索最近的邮件（包括已读和未读）
            status, messages = mail.search(None, 'ALL')
            
            if status != 'OK':
                return []
            
            # 获取所有邮件ID列表
            all_email_ids = messages[0].split()
            
            if not all_email_ids:
                return []
            
            # 只检查最新的50封邮件，避免处理太多历史邮件
            recent_email_ids = all_email_ids[-50:] if len(all_email_ids) > 50 else all_email_ids
            
            new_emails = []
            
            for email_id in recent_email_ids:
                try:
                    # 如果已经处理过这封邮件，跳过
                    email_id_str = email_id.decode()
                    if email_id_str in self.processed_emails:
                        continue
                    
                    # 获取邮件头信息来检查日期
                    status, header_data = mail.fetch(email_id, '(RFC822.HEADER)')
                    if status != 'OK':
                        continue
                    
                    # 解析邮件头
                    email_message = email.message_from_bytes(header_data[0][1])
                    
                    # 获取邮件接收时间
                    received_date_str = email_message.get('Date')
                    if received_date_str:
                        try:
                            # 解析邮件日期
                            received_date = email.utils.parsedate_to_datetime(received_date_str)
                            
                            # 统一时区处理：如果邮件日期有时区信息，转换为本地时区；如果没有，假设为本地时区
                            if received_date.tzinfo is not None:
                                # 转换为本地时间（无时区）
                                received_date = received_date.replace(tzinfo=None)
                            
                            # 只处理系统启动后收到的邮件
                            if received_date > self.system_start_time:
                                # 获取完整邮件内容
                                status, msg_data = mail.fetch(email_id, '(RFC822)')
                                
                                if status == 'OK':
                                    raw_email = msg_data[0][1]
                                    new_emails.append({
                                        'id': email_id_str,
                                        'raw_content': raw_email,
                                        'timestamp': received_date
                                    })
                                    print(f"🆕 发现新邮件: {email_id_str} (接收时间: {received_date.strftime('%Y-%m-%d %H:%M:%S')})")
                            
                            # 无论是否处理，都标记为已检查
                            self.processed_emails.add(email_id_str)
                            
                        except Exception as date_error:
                            print(f"⚠️ 解析邮件日期失败: {date_error}")
                            # 如果无法解析日期，标记为已处理避免重复检查
                            self.processed_emails.add(email_id_str)
                    else:
                        # 没有日期信息，标记为已处理
                        self.processed_emails.add(email_id_str)
                    
                except Exception as email_error:
                    print(f"⚠️ 检查邮件 {email_id} 时出错: {email_error}")
                    continue
            
            if new_emails:
                print(f"📬 发现 {len(new_emails)} 封系统启动后的新邮件")
            else:
                print("📭 没有发现系统启动后的新邮件")
            
            return new_emails
            
        except Exception as e:
            print(f"❌ 获取邮件失败: {e}")
            return []
    
    def save_email_as_eml(self, email_data):
        """保存邮件为.eml文件"""
        try:
            # 解析邮件获取基本信息
            msg = email.message_from_bytes(email_data['raw_content'])
            
            # 获取邮件主题作为文件名
            subject = msg.get('Subject', 'NoSubject')
            if subject:
                # 清理文件名中的特殊字符
                subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
                subject = subject[:50]  # 限制文件名长度
            
            # 生成.eml文件名
            timestamp = email_data['timestamp'].strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{subject}_{email_data['id']}.eml"
            filepath = os.path.join(self.save_directory, filename)
            
            # 保存为.eml文件
            with open(filepath, 'wb') as f:
                f.write(email_data['raw_content'])
            
            print(f"💾 邮件已保存: {filename}")
            
            return {
                'filepath': filepath,
                'filename': filename,
                'subject': subject,
                'email_id': email_data['id'],
                'timestamp': email_data['timestamp']
            }
            
        except Exception as e:
            print(f"❌ 保存邮件失败: {e}")
            return None
    
    def process_new_email(self, email_file_info):
        """处理新邮件 - 使用成功的解析器"""
        try:
            print(f"🔍 处理新邮件: {email_file_info['filename']}")
            
            # 使用已验证的邮件解析器
            parser = EmailParser()
            email_data = parser.load_eml_file(email_file_info['filepath'])
            
            if email_data:
                print(f"✅ 邮件解析成功!")
                print(f"   发件人: {email_data['info']['from']}")
                print(f"   主题: {email_data['info']['subject']}")
                print(f"   附件数量: {len(email_data['content']['attachments'])}")
                
                # 生成HTML显示文件
                html_path = email_file_info['filepath'].replace('.eml', '_display.html')
                html_content = parser.reconstruct_html_for_display(email_data['content'])
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"🌐 HTML显示文件已生成: {html_path}")
                
                return {
                    'email_data': email_data,
                    'html_path': html_path
                }
            
        except Exception as e:
            print(f"❌ 处理邮件失败: {e}")
            return None
    
    def monitor_emails_once(self):
        """执行一次邮件检查"""
        mail = self.connect_to_qq_imap()
        if not mail:
            return False
        
        try:
            # 获取新邮件
            new_emails = self.get_new_emails(mail)
            
            if new_emails:
                print(f"🚀 开始处理 {len(new_emails)} 封新邮件...")
                
                processed_emails = []
                
                for email_data in new_emails:
                    # 保存为.eml文件
                    file_info = self.save_email_as_eml(email_data)
                    
                    if file_info:
                        # 处理邮件（解析、生成HTML等）
                        processed_data = self.process_new_email(file_info)
                        
                        if processed_data:
                            print(f"✅ 邮件处理完成: {file_info['filename']}")
                            processed_emails.append(processed_data)
                
                return processed_emails
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
    
    def start_continuous_monitoring(self, check_interval=60):
        """启动连续监控模式"""
        print(f"🔄 启动邮件连续监控 (每{check_interval}秒检查一次)")
        self.is_monitoring = True
        
        def monitor_loop():
            while self.is_monitoring:
                try:
                    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 检查新邮件...")
                    result = self.monitor_emails_once()
                    
                    if result is not False:
                        if result:
                            print(f"✅ 处理了 {len(result)} 封新邮件")
                        else:
                            print("✅ 检查完成，无新邮件")
                    else:
                        print("⚠️ 检查失败")
                    
                    print(f"⏸️ 等待{check_interval}秒...")
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    print("\n🛑 用户中断监控")
                    self.is_monitoring = False
                    break
                except Exception as e:
                    print(f"❌ 监控循环出错: {e}")
                    print(f"⏸️ 等待{check_interval}秒后重试...")
                    time.sleep(check_interval)
        
        # 在后台线程中运行监控
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        return monitor_thread
    
    def stop_monitoring(self):
        """停止监控"""
        print("🛑 停止邮件监控...")
        self.is_monitoring = False

# 使用示例
def test_qq_monitor():
    """测试QQ邮箱监控"""
    print("🧪 测试QQ邮箱监控系统...")
    
    # 创建监控器
    monitor = QQEmailMonitor()
    
    # 测试连接
    print("\n🔗 测试连接...")
    mail = monitor.connect_to_qq_imap()
    if mail:
        print("✅ 连接测试成功！")
        mail.close()
        mail.logout()
        
        # 执行一次检查
        print("\n📬 执行一次邮件检查...")
        result = monitor.monitor_emails_once()
        
        if result is not False:
            print("✅ 监控测试成功！")
            return True
        else:
            print("❌ 监控测试失败")
            return False
    else:
        print("❌ 连接测试失败，请检查邮箱配置")
        return False

if __name__ == "__main__":
    test_qq_monitor()
