# -*- coding: utf-8 -*-
# 邮件发送模块
# 作者: justlovemaki
# 日期: 2025年8月28日

import resend
import base64
import os
from datetime import datetime
from typing import List, Dict, Optional

class EmailSender:
    """邮件发送类，封装Resend API"""
    
    def __init__(self, api_key: str = "re_6giBFioy_HW9cYt9xfR473x39HkuKtXT5"):
        """初始化邮件发送器"""
        resend.api_key = api_key
        self.api_key = api_key
        print(f"📧 邮件发送器已初始化")
    
    def send_email_with_attachments(self, 
                                  from_email: str, 
                                  to_email: str, 
                                  subject: str, 
                                  content: str,
                                  attachments: List[Dict] = None) -> Optional[str]:
        """
        发送带附件的邮件
        
        Args:
            from_email: 发件人邮箱
            to_email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容（支持HTML）
            attachments: 附件列表，格式：[{'filename': str, 'content': bytes}]
        
        Returns:
            邮件ID（成功）或None（失败）
        """
        try:
            print(f"📤 准备发送邮件")
            print(f"   发件人: {from_email}")
            print(f"   收件人: {to_email}")
            print(f"   主题: {subject}")
            print(f"   附件数量: {len(attachments) if attachments else 0}")
            
            # 构建邮件参数
            email_params = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": self._format_content(content)
            }
            
            # 添加附件
            if attachments:
                email_params["attachments"] = []
                for attachment in attachments:
                    # 将附件内容编码为base64
                    encoded_content = base64.b64encode(attachment['content']).decode('utf-8')
                    email_params["attachments"].append({
                        "filename": attachment['filename'],
                        "content": encoded_content
                    })
                    print(f"📎 添加附件: {attachment['filename']} ({len(attachment['content'])} 字节)")
            
            # 发送邮件
            email_result = resend.Emails.send(email_params)
            
            print(f"✅ 邮件发送成功！")
            print(f"   邮件ID: {email_result}")
            print(f"   发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return str(email_result)
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return None
    
    def send_simple_email(self, from_email: str, to_email: str, subject: str, content: str) -> Optional[str]:
        """
        发送简单邮件（无附件）
        """
        return self.send_email_with_attachments(from_email, to_email, subject, content, None)
    
    def _format_content(self, content: str) -> str:
        """
        格式化邮件内容
        将纯文本转换为HTML格式
        """
        if not content:
            return ""
        
        # 简单的文本到HTML转换
        html_content = content.replace('\n', '<br>')
        
        # 如果内容不包含HTML标签，添加基本的HTML结构
        if '<html>' not in html_content.lower() and '<body>' not in html_content.lower():
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    {html_content}
                </div>
            </body>
            </html>
            """
        
        return html_content
    
    def get_email_info(self, email_id: str) -> Optional[Dict]:
        """
        获取邮件信息
        """
        try:
            email_info = resend.Emails.get(email_id=email_id)
            return email_info
        except Exception as e:
            print(f"❌ 获取邮件信息失败: {e}")
            return None
    
    def send_batch_emails(self, email_list: List[Dict]) -> Optional[List]:
        """
        批量发送邮件
        
        Args:
            email_list: 邮件列表，每个元素包含from_email, to_email, subject, content
        """
        try:
            params = []
            for email_data in email_list:
                param = {
                    "from": email_data['from_email'],
                    "to": [email_data['to_email']],
                    "subject": email_data['subject'],
                    "html": self._format_content(email_data['content'])
                }
                params.append(param)
            
            result = resend.Batch.send(params)
            print(f"✅ 批量邮件发送成功: {len(email_list)} 封")
            return result
            
        except Exception as e:
            print(f"❌ 批量邮件发送失败: {e}")
            return None

# 创建全局邮件发送器实例
email_sender = EmailSender()

def send_email(from_email: str, to_email: str, subject: str, content: str, attachments: List[Dict] = None) -> Optional[str]:
    """
    便捷的邮件发送函数
    """
    return email_sender.send_email_with_attachments(from_email, to_email, subject, content, attachments)

if __name__ == "__main__":
    # 测试邮件发送
    print("🧪 测试邮件发送功能")
    
    # 发送测试邮件
    result = send_email(
        from_email="test@shiep.edu.kg",
        to_email="2846117874@qq.com",
        subject="测试邮件 - 新发送模块",
        content="这是来自新邮件发送模块的测试邮件。\n\n功能包括：\n- 支持附件发送\n- HTML格式化\n- 错误处理\n- 日志记录"
    )
    
    if result:
        print(f"🎉 测试成功，邮件ID: {result}")
    else:
        print("❌ 测试失败")
