#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支付监控系统 - 基于邮件通知的个人收款监控
"""

import imaplib
import email
import re
import json
import requests
from datetime import datetime, timedelta
import time
import threading

class PaymentMonitor:
    """支付监控器 - 基于支付宝邮件通知"""
    
    def __init__(self, email_config):
        self.email_config = email_config
        self.processed_payments = set()  # 防止重复处理
        self.running = False
        
    def start_monitor(self):
        """启动监控"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        print("💰 支付监控系统已启动")
        
    def stop_monitor(self):
        """停止监控"""
        self.running = False
        print("💰 支付监控系统已停止")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._check_payment_emails()
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                print(f"❌ 邮件监控错误: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
                
    def _check_payment_emails(self):
        """检查支付邮件"""
        try:
            # 连接邮箱
            mail = imaplib.IMAP4_SSL(
                self.email_config['imap_server'], 
                self.email_config['imap_port']
            )
            mail.login(
                self.email_config['username'], 
                self.email_config['password']
            )
            mail.select('INBOX')
            
            # 搜索支付宝收款邮件（最近1小时的）
            since_date = (datetime.now() - timedelta(hours=1)).strftime('%d-%b-%Y')
            search_criteria = f'(FROM "service@mail.alipay.com" SINCE "{since_date}")'
            
            typ, email_ids = mail.search(None, search_criteria)
            
            for email_id in email_ids[0].split():
                email_id = email_id.decode()
                if email_id not in self.processed_payments:
                    self._process_payment_email(mail, email_id)
                    self.processed_payments.add(email_id)
                    
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"❌ 邮件检查失败: {e}")
            
    def _process_payment_email(self, mail, email_id):
        """处理支付邮件"""
        try:
            typ, email_data = mail.fetch(email_id, '(RFC822)')
            email_message = email.message_from_bytes(email_data[0][1])
            
            # 解析邮件内容
            payment_info = self._parse_payment_email(email_message)
            
            if payment_info:
                print(f"💰 检测到支付: {payment_info}")
                
                # 匹配订单并处理充值
                self._handle_payment(payment_info)
                
        except Exception as e:
            print(f"❌ 处理邮件失败: {e}")
            
    def _parse_payment_email(self, email_message):
        """解析支付邮件内容"""
        try:
            subject = self._decode_header(email_message['Subject'])
            
            # 检查是否是收款通知
            if '收款' not in subject and '付款' not in subject:
                return None
                
            # 获取邮件正文
            body = self._get_email_body(email_message)
            
            # 解析金额
            amount_pattern = r'[¥￥]?(\d+\.?\d*)'
            amount_match = re.search(amount_pattern, body)
            
            # 解析备注/说明
            note_patterns = [
                r'付款说明[：:]\s*([^\n\r]+)',
                r'备注[：:]\s*([^\n\r]+)',
                r'商品[：:]\s*([^\n\r]+)'
            ]
            
            note = None
            for pattern in note_patterns:
                note_match = re.search(pattern, body)
                if note_match:
                    note = note_match.group(1).strip()
                    break
                    
            if amount_match:
                return {
                    'amount': float(amount_match.group(1)),
                    'note': note or '',
                    'time': datetime.now().isoformat(),
                    'raw_subject': subject
                }
                
        except Exception as e:
            print(f"❌ 解析邮件失败: {e}")
            
        return None
        
    def _get_email_body(self, email_message):
        """获取邮件正文"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() in ['text/plain', 'text/html']:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='ignore')
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
                
        return body
        
    def _decode_header(self, header):
        """解码邮件头"""
        if header is None:
            return ""
            
        decoded_parts = email.header.decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += str(part)
                
        return decoded_string
        
    def _handle_payment(self, payment_info):
        """处理支付信息"""
        try:
            # 根据备注信息匹配订单
            note = payment_info['note']
            amount = payment_info['amount']
            
            # 尝试从备注中提取订单号（支持易支付格式）
            order_id_patterns = [
                r'YP(\d{10,15})',  # 易支付订单号格式：YP + 时间戳 + 随机数
                r'ORDER(\d+)',      # 传统订单号格式
                r'订单[：:](\w+)',   # 中文订单号格式
                r'(\w*\d{10,}\w*)'  # 通用数字订单号
            ]

            order_id = None
            for pattern in order_id_patterns:
                order_match = re.search(pattern, note)
                if order_match:
                    if pattern.startswith('YP'):
                        order_id = f"YP{order_match.group(1)}"  # 重构完整的YP订单号
                    else:
                        order_id = order_match.group(1)
                    break

            if order_id:
                print(f"💰 匹配到订单: {order_id}, 金额: ¥{amount}")

                # 调用充值系统
                self._notify_recharge_system(order_id, amount, payment_info)
            else:
                print(f"⚠️ 未能匹配订单，备注: {note}")
                print(f"📧 邮件主题: {payment_info.get('raw_subject', '')}")
                # 尝试直接按金额处理（作为备用方案）
                print(f"🔄 尝试按金额匹配处理...")
                self._notify_recharge_system('AUTO_' + str(int(amount * 100)), amount, payment_info)
                
        except Exception as e:
            print(f"❌ 处理支付失败: {e}")
            
    def _notify_recharge_system(self, order_id, amount, payment_info):
        """通知充值系统"""
        try:
            # 调用您的Web系统API
            response = requests.post('http://127.0.0.1:5000/api/payment_notify', 
                json={
                    'order_id': order_id,
                    'amount': amount,
                    'payment_info': payment_info,
                    'source': 'email_monitor'
                }, 
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ 充值成功: 订单{order_id}, 金额¥{amount}")
            else:
                print(f"❌ 充值失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 通知充值系统失败: {e}")


# 使用示例
if __name__ == '__main__':
    # 邮箱配置（用于接收支付宝通知的邮箱）
    email_config = {
        'imap_server': 'imap.qq.com',
        'imap_port': 993,
        'username': 'your_email@qq.com',
        'password': 'your_password'  # 授权码
    }
    
    # 启动支付监控
    monitor = PaymentMonitor(email_config)
    monitor.start_monitor()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitor()
        print("程序退出")
