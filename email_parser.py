# -*- coding: utf-8 -*-
# 邮件解析器 - 解析和重构邮件显示
# 作者: justlovemaki
# 日期: 2025年8月22日
# 基于成功的解析经验整合

import email
import base64
import re
import os
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Dict, List, Optional, Tuple
import mimetypes

class EmailParser:
    """邮件解析器类 - 已验证可用的版本"""
    
    def __init__(self):
        self.extracted_images = []
        self.image_counter = 0
    
    def load_eml_file(self, eml_path: str) -> Dict:
        """加载.eml文件并返回解析结果"""
        print(f"📧 加载邮件文件: {eml_path}")
        
        try:
            with open(eml_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_email = f.read()
            
            # 解析邮件
            msg = email.message_from_string(raw_email)
            
            # 提取信息和内容
            info = self.extract_basic_info(msg)
            content = self.extract_content(msg)
            
            print("✅ 邮件文件加载和解析成功")
            
            return {
                'info': info,
                'content': content,
                'msg': msg
            }
            
        except Exception as e:
            print(f"❌ 加载邮件文件失败: {e}")
            return None
    
    def decode_header_value(self, header_value: str) -> str:
        """解码邮件头部信息"""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                except:
                    decoded_string += str(part)
            else:
                decoded_string += str(part)
        
        return decoded_string
    
    def extract_email_address(self, email_string: str) -> str:
        """从邮件地址字符串中提取纯邮箱地址"""
        if not email_string:
            return ""
        
        # 使用正则表达式提取 <email@domain> 格式中的邮箱地址
        import re
        
        # 匹配 <email@domain> 格式
        angle_bracket_match = re.search(r'<([^>]+)>', email_string)
        if angle_bracket_match:
            return angle_bracket_match.group(1).strip()
        
        # 如果没有尖括号，检查是否是纯邮箱地址
        # 简单的邮箱验证正则
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, email_string)
        if email_match:
            return email_match.group(0).strip()
        
        # 如果都不匹配，返回原始字符串
        return email_string.strip()
    
    def extract_basic_info(self, msg: email.message.Message) -> Dict:
        """提取邮件基本信息"""
        info = {
            'from': self.extract_email_address(self.decode_header_value(msg.get('From', ''))),
            'to': self.extract_email_address(self.decode_header_value(msg.get('To', ''))),
            'subject': self.decode_header_value(msg.get('Subject', '')),
            'date': msg.get('Date', ''),
            'message_id': msg.get('Message-ID', ''),
            'content_type': msg.get_content_type(),
        }
        
        # 检测Cloudflare转发信息
        x_forwarded_to = msg.get('X-Forwarded-To', '')
        x_forwarded_for = msg.get('X-Forwarded-For', '')
        
        if x_forwarded_to:
            info['forwarded_to'] = x_forwarded_to
            info['forwarded_from'] = x_forwarded_for
            print(f"📧 检测到Cloudflare转发: {x_forwarded_for} -> {x_forwarded_to}")
        
        return info
    
    def extract_content(self, msg: email.message.Message) -> Dict:
        """提取邮件内容"""
        content = {
            'text': '',
            'html': '',
            'attachments': [],
            'embedded_images': []
        }
        
        if msg.is_multipart():
            for part in msg.walk():
                self._process_email_part(part, content)
        else:
            self._process_email_part(msg, content)
        
        return content
    
    def _process_email_part(self, part: email.message.Message, content: Dict):
        """处理邮件的单个部分"""
        content_type = part.get_content_type()
        content_disposition = part.get('Content-Disposition', '')
        
        try:
            if content_type == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode('utf-8', errors='ignore')
                    content['text'] += text
                    
            elif content_type == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode('utf-8', errors='ignore')
                    content['html'] += html
                    
            elif content_type.startswith('image/'):
                self._process_image_part(part, content)
                
            elif 'attachment' in content_disposition:
                self._process_attachment(part, content)
                
        except Exception as e:
            print(f"⚠️ 处理邮件部分时出错: {e}")
    
    def _process_image_part(self, part: email.message.Message, content: Dict):
        """处理图片部分"""
        filename = part.get_filename()
        if not filename:
            ext = mimetypes.guess_extension(part.get_content_type()) or '.jpg'
            filename = f"image_{self.image_counter}{ext}"
            self.image_counter += 1
        
        image_data = part.get_payload(decode=True)
        if image_data:
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            image_info = {
                'filename': filename,
                'content_type': part.get_content_type(),
                'size': len(image_data),
                'base64_data': base64_data,
                'content_id': part.get('Content-ID', '').strip('<>')
            }
            
            content_disposition = part.get('Content-Disposition', '')
            if 'inline' in content_disposition or part.get('Content-ID'):
                content['embedded_images'].append(image_info)
            else:
                content['attachments'].append(image_info)
    
    def _process_attachment(self, part: email.message.Message, content: Dict):
        """处理附件"""
        filename = part.get_filename()
        if filename:
            filename = self.decode_header_value(filename)
            
            attachment_data = part.get_payload(decode=True)
            if attachment_data:
                attachment_info = {
                    'filename': filename,
                    'content_type': part.get_content_type(),
                    'size': len(attachment_data),
                    'data': base64.b64encode(attachment_data).decode('utf-8')
                }
                content['attachments'].append(attachment_info)
    
    def reconstruct_html_for_display(self, content: Dict) -> str:
        """重构HTML用于前端显示"""
        html = content.get('html', '')
        if not html and content.get('text'):
            html = f"<html><body><pre>{content['text']}</pre></body></html>"
        
        if not html:
            return "<html><body><p>无法解析邮件内容</p></body></html>"
        
        # 处理嵌入图片
        for img in content.get('embedded_images', []):
            if img.get('content_id'):
                cid_pattern = f"cid:{img['content_id']}"
                data_url = f"data:{img['content_type']};base64,{img['base64_data']}"
                html = html.replace(cid_pattern, data_url)
        
        # 添加样式
        html = self._add_display_styles(html)
        return html
    
    def _add_display_styles(self, html: str) -> str:
        """添加显示样式"""
        style = """
        <style>
            body { 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px; 
            }
            img { max-width: 100%; height: auto; }
            table { border-collapse: collapse; width: 100%; }
            .email-container {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                background: white;
            }
        </style>
        """
        
        if '<head>' in html:
            html = html.replace('<head>', f'<head>{style}')
        else:
            html = f"<html><head>{style}</head><body>{html}</body></html>"
        
        if '<body>' in html:
            html = html.replace('<body>', '<body><div class="email-container">')
            html = html.replace('</body>', '</div></body>')
        
        return html
    
    def parse_email_complete(self, eml_path: str, output_path: str = None) -> Dict:
        """完整的邮件解析流程"""
        print("🚀 开始完整邮件解析...")
        
        # 加载和解析邮件
        email_data = self.load_eml_file(eml_path)
        if not email_data:
            return None
        
        # 重构HTML
        reconstructed_html = self.reconstruct_html_for_display(email_data['content'])
        
        # 保存HTML文件
        if not output_path:
            output_path = eml_path.replace('.eml', '_reconstructed.html')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(reconstructed_html)
        
        return {
            'basic_info': email_data['info'],
            'content': email_data['content'],
            'reconstructed_html': reconstructed_html,
            'output_file': output_path
        }
