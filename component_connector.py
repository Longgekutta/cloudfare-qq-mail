# -*- coding: utf-8 -*-
"""
组件连接器
连接各个组件，实现完整的邮件监控系统
"""

import os
import sys
import json
import time
from datetime import datetime
from threading import Thread

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入各个组件
from realtime_monitor import RealtimeEmailMonitor
from email_parser import EmailParser
from database.db_manager import DatabaseManager
from email_config import EMAIL_SAVE_DIR, TARGET_DOMAIN

class ComponentConnector:
    """
    组件连接器
    连接邮件监控、解析、数据库存储等组件
    """
    
    def __init__(self):
        """初始化组件连接器"""
        self.monitor = RealtimeEmailMonitor()
        self.parser = EmailParser()
        self.db_manager = DatabaseManager()
        self.frontend_queue_dir = "./frontend_queue"
        
        # 确保前端队列目录存在
        os.makedirs(self.frontend_queue_dir, exist_ok=True)
        
        print("🔗 组件连接器已初始化")
        print(f"📊 前端队列目录: {self.frontend_queue_dir}")
    
    def start_monitoring(self):
        """启动邮件监控"""
        print("🔄 启动邮件监控...")
        self.monitor.start_monitoring()
    
    def process_email_to_database(self, email_id):
        """
        将邮件数据存储到数据库
        :param email_id: 邮件ID
        """
        try:
            # 读取前端队列中的邮件数据
            queue_file = os.path.join(self.frontend_queue_dir, f"{email_id}.json")
            if not os.path.exists(queue_file):
                print(f"❌ 邮件数据文件不存在: {queue_file}")
                return False
            
            with open(queue_file, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
            
            # 连接数据库
            if not self.db_manager.connect():
                print("❌ 数据库连接失败")
                return False
            
            try:
                # 提取邮件信息
                info = email_data.get('info', {})
                content = email_data.get('content', {})
                
                # 检查是否已经存在相同的邮件（基于发送者、接收者、主题和时间）
                sender_email = info.get('from', '')
                receiver_email = info.get('to', '')
                subject = info.get('subject', '')
                sent_time_str = info.get('date', '')
                
                # 解析邮件发送时间
                sent_time = None
                if sent_time_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        sent_time = parsedate_to_datetime(sent_time_str)
                    except:
                        sent_time = datetime.now()
                else:
                    sent_time = datetime.now()
                
                # 检查是否已存在相同的邮件
                existing_query = """
                SELECT id FROM emails 
                WHERE sender_email = %s AND receiver_email = %s AND subject = %s AND sent_time = %s
                LIMIT 1
                """
                existing_result = self.db_manager.execute_query(existing_query, (sender_email, receiver_email, subject, sent_time))
                
                if existing_result:
                    print(f"⏭️ 邮件 {email_id} 已存在于数据库中，跳过重复存储")
                    return True  # 返回True表示"处理成功"，避免重复处理
                
                # 重新解析.eml文件以获取完整的HTML内容
                email_parsed = None  # 初始化变量
                
                # 查找对应的EML文件
                import glob
                eml_filepath = None
                
                # 方法1: 按email_id查找
                eml_files = glob.glob(os.path.join(EMAIL_SAVE_DIR, f"*_{email_id}.eml"))
                if eml_files:
                    eml_filepath = eml_files[0]
                else:
                    # 方法2: 查找最新的EML文件（如果ID不匹配）
                    all_eml_files = glob.glob(os.path.join(EMAIL_SAVE_DIR, "*.eml"))
                    if all_eml_files:
                        # 按修改时间排序，取最新的
                        eml_filepath = max(all_eml_files, key=os.path.getmtime)
                        print(f"📧 未找到ID {email_id}对应的EML，使用最新文件: {eml_filepath}")
                
                if eml_filepath and os.path.exists(eml_filepath):
                    # 重新解析邮件以获取完整的HTML内容
                    email_parsed = self.parser.load_eml_file(eml_filepath)
                    if email_parsed and 'content' in email_parsed:
                        reconstructed_html = self.parser.reconstruct_html_for_display(email_parsed['content'])
                    else:
                        # 如果重新解析失败，使用原来的方法
                        reconstructed_html = self.parser.reconstruct_html_for_display(content)
                        email_parsed = None  # 确保变量状态正确
                else:
                    # 如果.eml文件不存在，使用原来的方法
                    reconstructed_html = self.parser.reconstruct_html_for_display(content)
                    email_parsed = None  # 确保变量状态正确
                
                # 获取最完整的邮件内容
                original_content = ''
                content_source = ""
                
                if email_parsed and 'content' in email_parsed:
                    # 优先使用原始HTML内容
                    html_content = email_parsed['content'].get('html', '')
                    text_content = email_parsed['content'].get('text', '')
                    
                    if html_content and len(html_content) > 100:
                        # 使用完整的原始HTML
                        original_content = html_content
                        content_source = "原始HTML"
                        print(f"📧 使用原始HTML内容，长度: {len(original_content)} 字符")
                    elif text_content and len(text_content) > 50:
                        # 如果只有文本，包装为HTML
                        original_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head><meta charset="utf-8"><title>邮件内容</title></head>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 20px;">
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">{text_content}</pre>
                        </body></html>
                        """
                        content_source = "文本包装"
                        print(f"📧 使用文本内容包装为HTML，长度: {len(original_content)} 字符")
                    else:
                        # 使用重构的HTML
                        original_content = reconstructed_html
                        content_source = "重构HTML"
                        print(f"📧 使用重构HTML，长度: {len(original_content)} 字符")
                else:
                    # 使用前端队列中的内容作为最后备选
                    queue_content = content.get('html', content.get('text', ''))
                    if queue_content and len(queue_content) > 50:
                        original_content = queue_content
                        content_source = "队列内容"
                        print(f"📧 使用队列内容，长度: {len(original_content)} 字符")
                    else:
                        original_content = reconstructed_html
                        content_source = "重构HTML(备选)"
                        print(f"📧 使用重构HTML作为最终备选，长度: {len(original_content)} 字符")
                
                print(f"🎯 最终内容源: {content_source}, 长度: {len(original_content)} 字符")
                
                # 保存邮件到数据库（使用原始HTML内容）
                email_db_id = self.db_manager.save_email(
                    sender_email=sender_email,
                    receiver_email=receiver_email,
                    subject=subject,
                    content=original_content,
                    sent_time=sent_time
                )
                
                if email_db_id > 0:
                    print(f"✅ 邮件数据已存储到数据库: {email_id}")
                    
                    # 处理附件信息
                    attachments = content.get('attachments', [])
                    if attachments:
                        print(f"📎 处理 {len(attachments)} 个附件...")
                        # 确保附件目录存在
                        attachments_dir = os.path.join(EMAIL_SAVE_DIR, 'attachments')
                        os.makedirs(attachments_dir, exist_ok=True)
                        
                        for attachment in attachments:
                            filename = attachment.get('filename', '')
                            file_size = attachment.get('size', 0)
                            content_type = attachment.get('content_type', '')
                            attachment_data = attachment.get('data', '')  # base64编码的数据
                            
                            # 生成附件文件路径
                            file_path = os.path.join(attachments_dir, filename)
                            
                            # 标准化路径分隔符为Windows格式
                            file_path = os.path.normpath(file_path)
                            
                            # 保存附件数据到文件
                            try:
                                import base64
                                decoded_data = base64.b64decode(attachment_data)
                                with open(file_path, 'wb') as f:
                                    f.write(decoded_data)
                                print(f"💾 附件文件已保存: {file_path}")
                                
                                # 标准化路径分隔符为Windows格式
                                normalized_file_path = os.path.normpath(file_path)
                                
                                # 保存附件信息到数据库
                                att_result = self.db_manager.create_attachment(
                                    email_id=email_db_id,
                                    filename=filename,
                                    file_path=normalized_file_path,
                                    file_size=file_size
                                )
                                
                                if att_result > 0:
                                    print(f"✅ 附件 '{filename}' 已存储到数据库")
                                else:
                                    print(f"❌ 附件 '{filename}' 存储到数据库失败")
                            except Exception as e:
                                print(f"❌ 保存附件 '{filename}' 时出错: {e}")
                    
                    return True
                else:
                    print(f"❌ 邮件数据存储失败: {email_id}")
                    return False
                    
            finally:
                # 断开数据库连接
                self.db_manager.disconnect()
                
        except Exception as e:
            print(f"❌ 处理邮件数据到数据库时出错: {e}")
            return False
    
    def process_frontend_data(self, email_id):
        """
        处理前端数据
        :param email_id: 邮件ID
        """
        try:
            # 读取前端队列中的邮件数据
            queue_file = os.path.join(self.frontend_queue_dir, f"{email_id}.json")
            if not os.path.exists(queue_file):
                print(f"❌ 邮件数据文件不存在: {queue_file}")
                return False
            
            with open(queue_file, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
            
            # 在这里可以添加更多的前端数据处理逻辑
            # 例如：数据验证、格式转换等
            
            print(f"✅ 前端数据处理完成: {email_id}")
            return True
            
        except Exception as e:
            print(f"❌ 处理前端数据时出错: {e}")
            return False
    
    def process_new_email(self, email_id):
        """
        处理新邮件的完整流程
        :param email_id: 邮件ID
        """
        print(f"🔄 开始处理新邮件: {email_id}")
        
        # 1. 处理前端数据
        if not self.process_frontend_data(email_id):
            print(f"❌ 前端数据处理失败: {email_id}")
            return False
        
        # 2. 存储邮件数据到数据库
        if not self.process_email_to_database(email_id):
            print(f"❌ 数据库存储失败: {email_id}")
            return False
        
        print(f"✅ 新邮件处理完成: {email_id}")
        return True
    
    def start_processing_worker(self):
        """
        启动处理工作线程
        监控前端队列目录，处理新邮件数据
        """
        print("🔧 启动处理工作线程...")
        
        processed_emails = set()  # 记录已处理的邮件ID
        
        # 检查数据库中已存在的邮件，避免重复处理
        if self.db_manager.connect():
            try:
                # 获取数据库中已存在的邮件数量
                existing_count_result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM emails")
                existing_count = existing_count_result[0]['count'] if existing_count_result else 0
                
                if existing_count > 0:
                    print(f"📊 发现 {existing_count} 封已处理的邮件，将跳过重复处理")
                    # 标记所有队列文件为已处理，避免重复处理
                    if os.path.exists(self.frontend_queue_dir):
                        for filename in os.listdir(self.frontend_queue_dir):
                            if filename.endswith('.json'):
                                email_id = filename[:-5]  # 去掉.json后缀
                                processed_emails.add(email_id)
            except Exception as e:
                print(f"⚠️ 检查已处理邮件时出错: {e}")
            finally:
                self.db_manager.disconnect()
        
        while True:
            try:
                # 检查前端队列目录中的新文件
                if os.path.exists(self.frontend_queue_dir):
                    for filename in os.listdir(self.frontend_queue_dir):
                        if filename.endswith('.json'):
                            email_id = filename[:-5]  # 去掉.json后缀
                            
                            # 跳过已处理的邮件
                            if email_id in processed_emails:
                                continue
                            
                            # 处理新邮件
                            if self.process_new_email(email_id):
                                processed_emails.add(email_id)
                
                # 每隔1秒检查一次
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ 处理工作线程出错: {e}")
                time.sleep(5)  # 出错后等待5秒再继续
    
    def start_full_system(self):
        """
        启动完整系统
        包括邮件监控和数据处理
        """
        print("🚀 启动完整邮件监控系统...")
        
        # 启动处理工作线程
        worker_thread = Thread(target=self.start_processing_worker, daemon=True)
        worker_thread.start()
        print("✅ 处理工作线程已启动")
        
        # 启动邮件监控
        self.start_monitoring()

def main():
    """主函数"""
    print("🚀 启动组件连接器")
    print("="*50)
    
    # 创建组件连接器
    connector = ComponentConnector()
    
    # 启动完整系统
    connector.start_full_system()

if __name__ == "__main__":
    main()
