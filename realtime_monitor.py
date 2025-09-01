# -*- coding: utf-8 -*-
# 实时邮件监控器 - 专门监控shiep.edu.kg域名邮件
# 每6秒检查一次，只处理新收到的目标域名邮件

import imaplib
import email
import os
import time
import json
import queue
import threading
import ssl
from datetime import datetime
from email_parser import EmailParser
from email_config import QQ_EMAIL, QQ_AUTH_CODE, EMAIL_SAVE_DIR, CHECK_INTERVAL, TARGET_DOMAIN, DEBUG_MODE

class RealtimeEmailMonitor:
    """
    实时邮件监控器
    专门监控特定域名的新邮件并实时处理
    """
    
    def __init__(self):
        self.email_account = QQ_EMAIL
        self.password = QQ_AUTH_CODE
        self.save_directory = EMAIL_SAVE_DIR
        self.target_domain = TARGET_DOMAIN
        self.check_interval = CHECK_INTERVAL
        
        # 连接配置
        self.imap_server = "imap.qq.com"
        self.imap_port = 993
        
        # 监控状态
        self.is_running = False
        self.start_time = datetime.now()  # 服务器启动时间 - 关键！
        self.processed_emails = set()  # 记录已处理的邮件ID
        self.last_check_time = self.start_time  # 上次检查时间
        self.last_email_id = None  # 记录上次检查的最新邮件ID
        self.consecutive_empty_checks = 0  # 连续空检查次数
        
        # 故障重试配置
        self.max_retry_attempts = 5
        self.retry_delay = 8  # 重试间隔(秒)
        
        # 异步处理队列配置
        self.email_queue = queue.Queue()  # 邮件处理队列
        self.processing_workers = 2  # 处理线程数量
        self.worker_threads = []  # 工作线程列表
        self.queue_stats = {
            'total_queued': 0,
            'total_processed': 0,
            'total_failed': 0,
            'current_queue_size': 0,
            'processing_threads_active': 0,
            'max_worker_threads': 2
        }
        
        # 解析器
        self.parser = EmailParser()
        
        # 创建目录
        os.makedirs(self.save_directory, exist_ok=True)
        os.makedirs("./frontend_queue", exist_ok=True)  # 前端队列目录
        
        print(f"🚀 实时邮件监控器已启动")
        print(f"📧 监控邮箱: {self.email_account}")
        print(f"🎯 目标域名: {self.target_domain}")
        print(f"⏰ 检查间隔: {self.check_interval}秒")
        print(f"🕐 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 保存目录: {self.save_directory}")
        print(f"� 异步处理线程: {self.processing_workers}个")
        print("�💡 只处理启动后收到的邮件")
        
        # 启动异步处理线程
        self.start_processing_workers()
    
    def start_processing_workers(self):
        """启动异步处理工作线程"""
        for i in range(self.processing_workers):
            worker = threading.Thread(
                target=self.email_processing_worker,
                name=f"EmailWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
            
        self.queue_stats['max_worker_threads'] = len(self.worker_threads)
        print(f"🔧 已启动 {len(self.worker_threads)} 个邮件处理线程")
    
    def email_processing_worker(self):
        """邮件处理工作线程"""
        worker_name = threading.current_thread().name
        
        while True:
            try:
                # 从队列获取邮件（阻塞等待）
                email_data = self.email_queue.get(timeout=30)
                
                if email_data is None:  # 停止信号
                    break
                
                # 更新统计
                self.queue_stats['processing_threads_active'] += 1
                self.queue_stats['current_queue_size'] = self.email_queue.qsize()
                
                if DEBUG_MODE:
                    print(f"🔧 [{worker_name}] 开始处理邮件 ID:{email_data['id']}")
                
                # 处理邮件（复用现有的成功逻辑）
                result = self.process_target_email(email_data)
                
                # 更新统计
                if result['success']:
                    self.queue_stats['total_processed'] += 1
                    print(f"✅ [{worker_name}] 邮件 {email_data['id']} 处理完成")
                else:
                    self.queue_stats['total_failed'] += 1
                    print(f"❌ [{worker_name}] 邮件 {email_data['id']} 处理失败: {result.get('error', 'Unknown')}")
                
                # 标记任务完成
                self.email_queue.task_done()
                self.queue_stats['processing_threads_active'] -= 1
                
            except queue.Empty:
                # 队列空闲，继续等待
                continue
            except Exception as e:
                print(f"❌ [{worker_name}] 处理线程出错: {e}")
                self.queue_stats['processing_threads_active'] -= 1
    
    def connect_to_imap(self):
        """连接到QQ邮箱IMAP - 带重试机制"""
        for attempt in range(self.max_retry_attempts):
            try:
                if DEBUG_MODE:
                    if attempt > 0:
                        print(f"� 重试连接QQ邮箱 (第{attempt+1}次)...")
                    else:
                        print("�🔗 连接QQ邮箱IMAP...")
                
                # 创建SSL上下文以解决协议兼容性问题
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=ssl_context)
                mail.login(self.email_account, self.password)
                mail.select('INBOX')
                
                if DEBUG_MODE:
                    print("✅ IMAP连接成功")
                return mail
                
            except Exception as e:
                print(f"❌ IMAP连接失败 (第{attempt+1}次): {e}")
                if attempt < self.max_retry_attempts - 1:
                    print(f"⏳ {self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("🚨 连接失败，已达到最大重试次数")
        
        return None
    
    def is_email_after_startup(self, msg_headers):
        """检查邮件是否在启动后收到"""
        try:
            # 获取邮件日期
            date_str = msg_headers.get('Date', '')
            if not date_str:
                return False
            
            # 解析邮件日期
            from email.utils import parsedate_tz, mktime_tz
            date_tuple = parsedate_tz(date_str)
            if date_tuple:
                email_timestamp = mktime_tz(date_tuple)
                email_datetime = datetime.fromtimestamp(email_timestamp)
                
                # 比较是否在启动时间之后
                is_after = email_datetime > self.start_time
                
                if DEBUG_MODE and is_after:
                    print(f"📧 新邮件时间: {email_datetime.strftime('%H:%M:%S')} (启动后 {(email_datetime - self.start_time).total_seconds():.0f}秒)")
                
                return is_after
            
            return False
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ 解析邮件时间失败: {e}")
            return False
    
    def is_target_email(self, email_headers):
        """检查是否是目标邮件"""
        try:
            # 检查收件人地址
            to_field = email_headers.get('To', '').lower()
            cc_field = email_headers.get('Cc', '').lower()
            
            # 检查是否包含目标域名
            target_found = (
                self.target_domain.lower() in to_field or 
                self.target_domain.lower() in cc_field
            )
            
            if DEBUG_MODE and target_found:
                print(f"🎯 发现目标邮件: To={to_field}")
            
            return target_found
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ 检查邮件头部失败: {e}")
            return False
    
    def get_new_target_emails(self, mail):
        """获取启动后收到的目标邮件 - 优化版"""
        try:
            # 搜索所有邮件，不限于未读
            status, messages = mail.search(None, 'ALL')
            
            if status != 'OK' or not messages[0]:
                return []
            
            email_ids = messages[0].split()
            
            if not email_ids:
                return []
            
            # 智能确定检查范围
            if self.last_email_id is None:
                # 首次运行，检查最近10封即可
                check_range = email_ids[-10:]
                if DEBUG_MODE:
                    print(f"📬 首次检查最近 {len(check_range)} 封邮件...")
            else:
                # 找到上次检查位置，只检查新的邮件
                try:
                    last_id_bytes = self.last_email_id.encode()
                    if last_id_bytes in email_ids:
                        last_index = email_ids.index(last_id_bytes)
                        check_range = email_ids[last_index + 1:]  # 只检查新邮件
                        if DEBUG_MODE:
                            print(f"📬 检查 {len(check_range)} 封新邮件...")
                    else:
                        # 找不到上次位置，检查最近10封
                        check_range = email_ids[-10:]
                        if DEBUG_MODE:
                            print(f"📬 未找到上次位置，检查最近 {len(check_range)} 封邮件...")
                except:
                    check_range = email_ids[-10:]
                    if DEBUG_MODE:
                        print(f"📬 回退策略，检查最近 {len(check_range)} 封邮件...")
            
            # 更新最新邮件ID
            if email_ids:
                self.last_email_id = email_ids[-1].decode()
            
            # 如果没有新邮件要检查
            if not check_range:
                if DEBUG_MODE:
                    print("📭 没有新邮件需要检查")
                return []
            
            target_emails = []
            checked_count = 0
            
            for email_id in reversed(check_range):  # 从最新的开始检查
                email_id_str = email_id.decode()
                checked_count += 1
                
                # 跳过已处理的邮件
                if email_id_str in self.processed_emails:
                    continue
                
                # 获取邮件头部信息
                status, header_data = mail.fetch(email_id, '(BODY[HEADER])')
                
                if status == 'OK':
                    header_content = header_data[0][1].decode('utf-8', errors='ignore')
                    headers = email.message_from_string(header_content)
                    
                    # 先检查时间 - 如果太老就跳过
                    if not self.is_email_after_startup(headers):
                        continue
                    
                    # 再检查是否是目标邮件
                    if self.is_target_email(headers):
                        # 获取完整邮件内容
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            raw_email = msg_data[0][1]
                            target_emails.append({
                                'id': email_id_str,
                                'raw_content': raw_email,
                                'timestamp': datetime.now(),
                                'headers': headers
                            })
                            
                            # 记录为已处理
                            self.processed_emails.add(email_id_str)
                            
                            print(f"🎯 收到目标邮件 ID:{email_id_str}")
            
            if DEBUG_MODE:
                if target_emails:
                    print(f"📊 检查了 {checked_count} 封邮件，找到 {len(target_emails)} 封目标邮件")
                    self.consecutive_empty_checks = 0
                else:
                    self.consecutive_empty_checks += 1
                    if self.consecutive_empty_checks <= 3:  # 只在前几次显示详细信息
                        print(f"📊 检查了 {checked_count} 封邮件，暂无目标邮件")
            
            return target_emails
            
        except Exception as e:
            print(f"❌ 获取邮件失败: {e}")
            return []
    
    def process_target_email(self, email_data):
        """处理目标邮件"""
        try:
            print(f"🔄 处理目标邮件 ID:{email_data['id']}")
            
            # 解析邮件头部信息
            headers = email_data['headers']
            subject = headers.get('Subject', 'No Subject')
            from_addr = headers.get('From', 'Unknown')
            to_addr = headers.get('To', 'Unknown')
            
            print(f"📧 邮件信息:")
            print(f"   发件人: {from_addr}")
            print(f"   收件人: {to_addr}")
            print(f"   主题: {subject}")
            
            # 保存为.eml文件
            timestamp = email_data['timestamp'].strftime("%Y%m%d_%H%M%S")
            safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
            filename = f"{timestamp}_{safe_subject}_{email_data['id']}.eml"
            filepath = os.path.join(self.save_directory, filename)
            
            with open(filepath, 'wb') as f:
                f.write(email_data['raw_content'])
            
            print(f"💾 邮件已保存: {filename}")
            
            # 使用解析器解析邮件
            email_parsed = self.parser.load_eml_file(filepath)
            
            if email_parsed:
                print("✅ 邮件解析成功")
                
                # 生成HTML显示
                html_content = self.parser.reconstruct_html_for_display(email_parsed['content'])
                html_path = filepath.replace('.eml', '_display.html')
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 准备前端数据
                frontend_data = {
                    'id': email_data['id'],
                    'timestamp': email_data['timestamp'].isoformat(),
                    'info': email_parsed['info'],
                    'content': {
                        'text': email_parsed['content']['text'][:1000],  # 限制长度
                        'html_path': html_path,
                        'attachments': [
                            {
                                'filename': att['filename'],
                                'size': att['size'],
                                'content_type': att['content_type']
                            } for att in email_parsed['content']['attachments']
                        ]
                    },
                    'processed_time': datetime.now().isoformat()
                }
                
                # 保存到前端队列
                queue_file = f"./frontend_queue/{email_data['id']}.json"
                with open(queue_file, 'w', encoding='utf-8') as f:
                    json.dump(frontend_data, f, ensure_ascii=False, indent=2)
                
                print(f"📤 前端数据已准备: {queue_file}")
                print(f"🌐 HTML显示文件: {html_path}")
                
                return {
                    'success': True,
                    'eml_path': filepath,
                    'html_path': html_path,
                    'frontend_data': frontend_data
                }
            else:
                print("❌ 邮件解析失败")
                return {'success': False, 'error': 'Parse failed'}
                
        except Exception as e:
            print(f"❌ 处理邮件失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def monitor_once(self):
        """执行一次监控 - 带重试机制和异步处理"""
        mail = self.connect_to_imap()
        if not mail:
            print("🚨 无法连接到邮箱，跳过本次检查")
            return []
        
        try:
            target_emails = self.get_new_target_emails(mail)
            
            if target_emails:
                print(f"🚀 发现 {len(target_emails)} 封目标邮件，加入处理队列...")
                
                # 将邮件加入异步处理队列（快速）
                for email_data in target_emails:
                    self.email_queue.put(email_data)
                    self.queue_stats['total_queued'] += 1
                
                # 显示队列状态
                queue_size = self.email_queue.qsize()
                active_workers = self.queue_stats['processing_threads_active']
                print(f"📊 队列状态: {queue_size} 待处理, {active_workers} 线程工作中")
                
                return len(target_emails)  # 返回加入队列的数量
            
            else:
                if DEBUG_MODE and self.consecutive_empty_checks <= 3:
                    print("📭 暂无新的目标邮件")
                elif self.consecutive_empty_checks == 4:
                    print("📭 持续无新邮件，减少日志输出...")
            
            return 0
            
        except Exception as e:
            print(f"❌ 监控过程出错: {e}")
            return 0
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
    
    def start_monitoring(self):
        """启动持续监控"""
        # 启动异步工作线程（如果还未启动）
        if not getattr(self, 'workers_running', False):
            self.start_processing_workers()
        
        print(f"🔄 启动持续监控 (每{self.check_interval}秒检查一次)")
        print(f"🚀 异步队列处理: 开启 ({self.queue_stats['max_worker_threads']} 工作线程)")
        print("按 Ctrl+C 停止监控")
        print("="*60)
        
        self.is_running = True
        total_queued = 0
        
        try:
            while self.is_running:
                check_time = datetime.now().strftime('%H:%M:%S')
                if DEBUG_MODE:
                    print(f"\n⏰ [{check_time}] 检查新邮件...")
                
                # monitor_once现在返回加入队列的邮件数量
                queued_count = self.monitor_once()
                
                if queued_count:
                    total_queued += queued_count
                    queue_size = self.email_queue.qsize()
                    processed = self.queue_stats['total_processed']
                    print(f"📊 本次入队: {queued_count} 封 | 队列待处理: {queue_size} 封 | 已处理: {processed} 封")
                
                # 等待下次检查
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 用户停止监控")
        except Exception as e:
            print(f"\n❌ 监控循环出错: {e}")
        finally:
            self.is_running = False
            duration = datetime.now() - self.start_time
            print(f"\n📊 监控结束统计:")
            print(f"   运行时间: {duration}")
            print(f"   处理邮件: {total_processed} 封")
            print(f"   已处理ID: {len(self.processed_emails)} 个")

def main():
    """主函数"""
    print("🚀 启动实时邮件监控系统")
    print("="*60)
    print(f"🎯 专门监控 {TARGET_DOMAIN} 域名邮件")
    print(f"⏰ 每 {CHECK_INTERVAL} 秒检查一次")
    print(f"🔄 异步队列处理: 多线程并行处理")
    print("="*60)
    
    monitor = RealtimeEmailMonitor()
    
    # 测试连接
    print("\n🧪 测试连接...")
    mail = monitor.connect_to_imap()
    if mail:
        print("✅ 连接测试成功")
        mail.close()
        mail.logout()
        
        print("\n🔄 开始监控...")
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，正在安全关闭...")
            monitor.is_running = False
        except Exception as e:
            print(f"❌ 监控系统错误: {e}")
        finally:
            # 显示最终统计
            if hasattr(monitor, 'queue_stats'):
                stats = monitor.queue_stats
                print(f"\n📊 最终统计:")
                print(f"   总入队邮件: {stats['total_queued']}")
                print(f"   总处理成功: {stats['total_processed']}")
                print(f"   总处理失败: {stats['total_failed']}")
            print("👋 监控系统已关闭")
    else:
        print("❌ 连接失败，请检查配置")

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'workers_running') and self.workers_running:
            print("🛑 正在停止工作线程...")
            self.workers_running = False
            
            # 发送停止信号到队列
            for _ in range(self.queue_stats['max_worker_threads']):
                self.email_queue.put(None)
            
            # 等待线程结束
            if hasattr(self, 'worker_threads'):
                for thread in self.worker_threads:
                    if thread.is_alive():
                        thread.join(timeout=5.0)
            
            print("✅ 工作线程已停止")

if __name__ == "__main__":
    main()
