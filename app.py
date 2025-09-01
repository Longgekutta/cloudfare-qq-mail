# -*- coding: utf-8 -*-
"""
Flask Web应用主文件
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file, Response
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库管理模块
from database.db_manager import DatabaseManager

# 导入系统配置
from config import Config

# 导入易支付相关模块
from yipay_utils import YiPayUtil
from yipay_config import PAYMENT_TYPES, YIPAY_PID, YIPAY_KEY

# 创建Flask应用
app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = 'cloudfare_qq_mail_secret_key_2025'  # 在生产环境中应该使用更安全的密钥

# 创建数据库管理器实例
# 注意：DatabaseManager内部使用连接池，支持多线程
db_manager = DatabaseManager()

# 统一密码验证函数
def verify_password(plain_password, hashed_password, user_id=None):
    """
    统一的密码验证函数
    Args:
        plain_password: 明文密码
        hashed_password: 存储的哈希密码
        user_id: 用户ID（用于自动升级密码）
    Returns:
        bool: 密码是否正确
    """
    import bcrypt
    import hashlib

    try:
        # 优先尝试bcrypt验证
        if hashed_password.startswith('$2b$'):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # 兼容旧的SHA256密码
            password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            is_valid = (hashed_password == password_hash)

            # 如果SHA256验证成功且提供了user_id，自动升级到bcrypt
            if is_valid and user_id and db_manager.connect():
                try:
                    new_hash = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    db_manager.update_user_password(user_id, new_hash)
                    print(f"用户ID {user_id} 的密码已自动升级到bcrypt")
                except Exception as e:
                    print(f"密码升级失败: {str(e)}")
                finally:
                    db_manager.disconnect()

            return is_valid

    except Exception as e:
        print(f"密码验证异常: {str(e)}")
        return False

def hash_password(plain_password):
    """
    统一的密码哈希函数
    Args:
        plain_password: 明文密码
    Returns:
        str: bcrypt哈希密码
    """
    import bcrypt
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 首页路由
@app.route('/')
def index():
    """
    首页视图函数
    """
    # 检查用户是否已登录
    if 'user_id' in session:
        # 用户已登录，获取用户信息
        user = None
        if db_manager.connect():
            user = db_manager.get_user_by_username(session['username'])
            db_manager.disconnect()
        
        # 渲染首页模板，传递用户信息
        return render_template('index.html', user=user)
    else:
        # 用户未登录，渲染首页模板，不传递用户信息
        return render_template('index.html', user=None)

# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    登录页面视图函数
    """
    if request.method == 'POST':
        # 处理登录表单提交
        username = request.form['username']
        password = request.form['password']
        
        # 验证用户名和密码
        user = None
        if db_manager.connect():
            user = db_manager.get_user_by_username(username)
            db_manager.disconnect()
        
        # 检查用户是否存在并且密码正确
        if user:
            # 使用统一的密码验证函数
            if verify_password(password, user['password'], user['id']):
                # 登录成功，设置会话
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                # 密码错误
                return render_template('login.html', error='用户名或密码错误')
        else:
            # 用户不存在
            return render_template('login.html', error='用户名或密码错误')
    
    # GET请求，渲染登录页面
    return render_template('login.html')

# 注册页面路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    注册页面视图函数
    """
    if request.method == 'POST':
        # 处理注册表单提交
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        registration_code = request.form['registration_code'].strip()
        
        # 检查密码是否匹配
        if password != confirm_password:
            return render_template('register.html', error='密码不匹配')
        
        # 验证注册码
        if not registration_code:
            return render_template('register.html', error='请输入注册码')

        # 对密码进行统一加密
        hashed_password = hash_password(password)

        # 使用原子操作注册用户
        if db_manager.connect():
            try:
                result = db_manager.register_user_with_code(username, hashed_password, registration_code)

                if result['success']:
                    print(f"✅ 用户 {username} 注册成功，使用注册码 {registration_code}")
                    return redirect(url_for('login'))
                else:
                    return render_template('register.html', error=result['message'])

            except Exception as e:
                print(f"❌ 注册过程异常: {str(e)}")
                return render_template('register.html', error='注册过程出现异常，请重试')
            finally:
                db_manager.disconnect()
        else:
            return render_template('register.html', error='数据库连接失败，请重试')
    
    # GET请求，渲染注册页面
    return render_template('register.html')

# 退出登录路由
@app.route('/logout')
def logout():
    """
    退出登录视图函数
    """
    # 清除会话
    session.clear()
    # 重定向到首页
    return redirect(url_for('index'))

# 邮件列表页面路由
@app.route('/mails')
def mails():
    """
    邮件列表页面视图函数 - 支持邮箱过滤和翻页
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取过滤参数和翻页参数
    email_filter = request.args.get('email', '')
    page = int(request.args.get('page', 1))
    per_page = 20  # 每页显示20封邮件
    offset = (page - 1) * per_page
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 获取邮件列表和总数 - 根据用户权限决定
    mail_list = []
    total_count = 0
    if db_manager.connect():
        if user and user.get('is_admin', False):
            # 管理员可以看到所有邮件
            if email_filter == '__ALL__':
                # 管理员选择"全部"，显示所有用户的邮件
                mail_list = db_manager.get_all_emails_for_admin(per_page, offset)
                total_count = db_manager.get_all_emails_count_for_admin()
            elif email_filter:
                # 按特定邮箱过滤
                mail_list = db_manager.get_emails_by_email_filter(email_filter, per_page, offset)
                total_count = db_manager.get_emails_count_by_email_filter(email_filter)
            else:
                # 管理员默认看到该管理员创建的邮箱邮件
                mail_list = db_manager.get_admin_created_emails(user['id'], per_page, offset)
                total_count = db_manager.get_admin_created_emails_count(user['id'])
        elif user and user.get('is_vip', False):
            # VIP用户可以看到所有邮件
            if email_filter:
                mail_list = db_manager.get_emails_by_email_filter(email_filter, per_page, offset)
                total_count = db_manager.get_emails_count_by_email_filter(email_filter)
            else:
                mail_list = db_manager.get_emails(per_page, offset)
                total_count = db_manager.get_emails_count()
        else:
            # 普通用户只能看到与自己相关的邮件
            if email_filter:
                mail_list = db_manager.get_user_emails_with_isolation_by_email_filter(session['user_id'], email_filter, per_page, offset)
                total_count = db_manager.get_user_emails_count_with_isolation_by_email_filter(session['user_id'], email_filter)
            else:
                mail_list = db_manager.get_user_emails_with_isolation(session['user_id'], per_page, offset)
                total_count = db_manager.get_user_emails_count_with_isolation(session['user_id'])
        db_manager.disconnect()
    
    # 计算翻页信息
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    # 获取用户的已注册邮箱用于过滤器
    user_emails = []
    if db_manager.connect():
        if user and user.get('is_vip', False):
            # 管理员可以看到所有邮箱
            user_emails = db_manager.get_all_user_emails()
        else:
            # 普通用户只能看到自己的邮箱
            user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    # 渲染邮件列表页面模板
    return render_template('mails.html', 
                         mails=mail_list, 
                         user=user, 
                         user_emails=user_emails, 
                         current_email=email_filter,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         prev_page=prev_page,
                         next_page=next_page,
                         total_count=total_count)

# 邮件详情页面路由
@app.route('/mail/<int:mail_id>')
def mail_detail(mail_id):
    """
    邮件详情页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 获取邮件详情 - 根据用户权限决定
    mail = {}
    if db_manager.connect():
        if user and user.get('is_vip', False):
            # 管理员可以看到所有邮件详情
            mail = db_manager.get_email_by_id(mail_id)
        else:
            # 普通用户只能看到与自己相关的邮件详情
            mail = db_manager.get_user_email_by_id_with_isolation(mail_id, session['user_id'])
        db_manager.disconnect()
    
    # 如果邮件不存在或用户无权访问，返回404
    if not mail:
        return "邮件不存在或无权访问", 404
    
    # 渲染邮件详情页面模板
    return render_template('mail_detail.html', mail=mail, user=user)

# 全新的原始邮件显示路由 - 完全基于EML文件
@app.route('/mail/<int:mail_id>/pure')
def mail_pure_content(mail_id):
    """
    显示纯净的原始邮件HTML内容 - 直接从EML提取，不经过任何处理
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return "未授权访问", 401
    
    try:
        # 根据邮件ID查找对应的EML文件
        import glob
        eml_files = glob.glob(f"./received_emails/*_{mail_id}.eml")
        
        if eml_files:
            # 直接读取EML文件
            with open(eml_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                eml_content = f.read()
            
            # 解析邮件获取HTML内容
            import email
            msg = email.message_from_string(eml_content)
            
            # 提取HTML内容
            html_content = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_content = payload.decode('utf-8', errors='ignore')
                            break
            else:
                if msg.get_content_type() == "text/html":
                    payload = msg.get_payload(decode=True)
                    if payload:
                        html_content = payload.decode('utf-8', errors='ignore')
            
            if html_content:
                # 直接返回原始HTML，保持完全一模一样
                return html_content
            else:
                return "<p>此邮件不包含HTML内容</p>"
        else:
            return "<p>未找到对应的EML文件</p>"
            
    except Exception as e:
        return f"<p>读取邮件失败: {str(e)}</p>"

# 添加EML原始文件查看路由
@app.route('/mail/<int:mail_id>/eml')
def mail_eml_view(mail_id):
    """
    查看原始EML文件内容
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return "未授权访问", 401
    
    # 权限检查（简化版）
    import glob
    eml_files = glob.glob(f"./received_emails/*_{mail_id}.eml")
    
    if not eml_files:
        return "EML文件不存在", 404
    
    try:
        with open(eml_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            eml_content = f.read()
        
        # 返回纯文本格式的EML内容
        from flask import Response
        return Response(eml_content, mimetype='text/plain; charset=utf-8')
        
    except Exception as e:
        return f"无法读取EML文件: {str(e)}", 500

# 邮件原始内容显示路由
@app.route('/mail/<int:mail_id>/raw')
def mail_raw_content(mail_id):
    """
    显示邮件原始HTML内容
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return "未授权访问", 401
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 获取邮件详情 - 根据用户权限决定
    mail = {}
    if db_manager.connect():
        if user and user.get('is_vip', False):
            # 管理员可以看到所有邮件详情
            mail = db_manager.get_email_by_id(mail_id)
        else:
            # 普通用户只能看到与自己相关的邮件详情
            mail = db_manager.get_user_email_by_id_with_isolation(mail_id, session['user_id'])
        db_manager.disconnect()
    
    # 如果邮件不存在或用户无权访问，返回404
    if not mail:
        return "邮件不存在或无权访问", 404
    
    # 尝试读取原始EML文件并完整显示
    try:
        # 根据邮件ID查找对应的EML文件
        import glob
        eml_files = glob.glob(f"./received_emails/*_{mail_id}.eml")
        
        if eml_files:
            # 直接读取并解析EML文件，生成完整的邮件视图
            eml_content = ""
            with open(eml_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                eml_content = f.read()
            
            # 解析邮件
            import email
            from email.header import decode_header
            msg = email.message_from_string(eml_content)
            
            # 构建完整的邮件视图
            html_output = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>邮件详情</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        margin: 20px;
                        background: #f5f5f5;
                    }
                    .email-container {
                        background: white;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 20px;
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    .email-header {
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                        border-left: 4px solid #007bff;
                    }
                    .email-content {
                        border: 1px solid #e9ecef;
                        padding: 20px;
                        border-radius: 5px;
                        background: white;
                    }
                    .header-item {
                        margin: 5px 0;
                    }
                    .header-label {
                        font-weight: bold;
                        color: #495057;
                        display: inline-block;
                        width: 100px;
                    }
                    .raw-content {
                        white-space: pre-wrap;
                        font-family: monospace;
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        border: 1px solid #e9ecef;
                        margin-top: 20px;
                        font-size: 12px;
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h2>📧 邮件详情</h2>"""
            
            # 添加邮件头部信息
            def decode_mime_header(header_value):
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
                        except Exception as e:
                            print(f"⚠️ 解码MIME头部失败: {e}")
                            decoded_string += str(part)
                    else:
                        decoded_string += str(part)
                return decoded_string
            
            html_output += f'<div class="header-item"><span class="header-label">发件人:</span> {decode_mime_header(msg.get("From", ""))}</div>'
            html_output += f'<div class="header-item"><span class="header-label">收件人:</span> {decode_mime_header(msg.get("To", ""))}</div>'
            html_output += f'<div class="header-item"><span class="header-label">主题:</span> {decode_mime_header(msg.get("Subject", ""))}</div>'
            html_output += f'<div class="header-item"><span class="header-label">时间:</span> {msg.get("Date", "")}</div>'
            html_output += "</div>"
            
            # 提取并显示邮件内容
            html_content = ""
            text_content = ""
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_content = payload.decode('utf-8', errors='ignore')
                    elif content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            text_content = payload.decode('utf-8', errors='ignore')
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    content = payload.decode('utf-8', errors='ignore')
                    if content_type == "text/html":
                        html_content = content
                    else:
                        text_content = content
            
            # 显示邮件内容
            html_output += '<div class="email-content">'
            if html_content:
                html_output += '<h3>HTML内容:</h3>'
                html_output += html_content
            elif text_content:
                html_output += '<h3>文本内容:</h3>'
                html_output += f'<pre style="white-space: pre-wrap;">{text_content}</pre>'
            else:
                html_output += '<p>无邮件内容</p>'
            html_output += '</div>'
            
            # 显示原始邮件源码（用户要求的"一模一样"）
            html_output += f'''
                <details style="margin-top: 20px;">
                    <summary style="cursor: pointer; font-weight: bold; color: #007bff;">🔍 查看原始邮件源码（完全一模一样）</summary>
                    <div class="raw-content">{eml_content}</div>
                </details>
            '''
            
            html_output += """
                </div>
            </body>
            </html>
            """
            
            return html_output
        else:
            # 如果没有EML文件，返回数据库中的内容
            content = mail.get('content', '无内容')
            if not content.startswith('<html'):
                content = f"<html><body><pre style='white-space: pre-wrap; font-family: Arial, sans-serif;'>{content}</pre></body></html>"
            return content
            
    except Exception as e:
        return f"<html><body><p>无法加载邮件内容: {str(e)}</p></body></html>"

# 用户管理页面路由（仅管理员可见）
@app.route('/admin/users')
def admin_users():
    """
    用户管理页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查用户是否为管理员
    # 这里需要根据实际需求实现管理员权限检查逻辑
    # 暂时假设所有登录用户都是管理员
    
    # 获取用户列表
    user_list = []
    if db_manager.connect():
        user_list = db_manager.get_all_users()
        db_manager.disconnect()
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染用户管理页面模板
    return render_template('admin_users.html', users=user_list, user=user)

# 域名管理页面路由（仅管理员可见）
@app.route('/admin/domains')
def admin_domains():
    """
    域名管理页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查用户是否为管理员
    # 这里需要根据实际需求实现管理员权限检查逻辑
    # 暂时假设所有登录用户都是管理员
    
    # 获取域名列表
    domain_list = []
    if db_manager.connect():
        domain_list = db_manager.get_all_domains()
        db_manager.disconnect()
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染域名管理页面模板
    return render_template('admin_domains.html', domains=domain_list, user=user)

# 注册码管理页面路由（仅管理员可见）
@app.route('/admin/codes')
def admin_codes():
    """
    注册码管理页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user.get('is_vip', False):
        return "权限不足", 403
    
    # 获取翻页参数
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # 获取注册码列表和总数
    codes_list = []
    total_count = 0
    if db_manager.connect():
        codes_list = db_manager.get_registration_codes(per_page, offset)
        total_count = db_manager.get_registration_codes_count()
        db_manager.disconnect()
    
    # 计算翻页信息
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    # 渲染注册码管理页面模板
    return render_template('admin_codes.html', 
                         codes=codes_list, 
                         user=user,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         prev_page=prev_page,
                         next_page=next_page,
                         total_count=total_count)

# 生成注册码路由
@app.route('/admin/codes/generate', methods=['POST'])
def generate_code():
    """
    生成注册码
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()

    if not user or not user.get('is_admin', False):
        return "权限不足", 403

    # 获取表单数据
    description = request.form.get('description', '')
    count = int(request.form.get('count', 1))

    # 检查数量限制
    if count > 500:
        return redirect(url_for('admin_codes') + '?error=count_limit_exceeded')
    
    # 生成注册码
    import random
    import string
    from datetime import datetime
    
    generated_codes = []
    if db_manager.connect():
        for i in range(count):
            # 生成8位随机注册码
            code = 'REG' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # 确保注册码唯一
            while db_manager.get_registration_code_by_code(code):
                code = 'REG' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # 创建注册码
            if db_manager.create_registration_code(code, description, user['id']):
                generated_codes.append(code)
        
        db_manager.disconnect()
    
    if generated_codes:
        return redirect(url_for('admin_codes') + f'?success=generated_{len(generated_codes)}_codes')
    else:
        return redirect(url_for('admin_codes') + '?error=generation_failed')

# 删除注册码路由
@app.route('/admin/codes/delete/<code>', methods=['POST'])
def delete_code(code):
    """
    删除注册码
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user.get('is_admin', False):
        return "权限不足", 403
    
    # 删除注册码
    if db_manager.connect():
        db_manager.delete_registration_code(code)
        db_manager.disconnect()
    
    return redirect(url_for('admin_codes') + '?success=code_deleted')

# 批量删除已使用注册码路由
@app.route('/admin/codes/delete_used', methods=['POST'])
def delete_used_codes():
    """
    批量删除所有已使用的注册码
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()

    if not user or not user.get('is_admin', False):
        return "权限不足", 403

    # 批量删除已使用的注册码
    deleted_count = 0
    if db_manager.connect():
        deleted_count = db_manager.delete_used_registration_codes()
        db_manager.disconnect()

    if deleted_count > 0:
        return redirect(url_for('admin_codes') + f'?success=deleted_{deleted_count}_used_codes')
    else:
        return redirect(url_for('admin_codes') + '?info=no_used_codes_to_delete')

# 管理员用户操作API
@app.route('/api/admin/users/add', methods=['POST'])
def api_add_user():
    """添加用户API"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
        if not user or not user.get('is_admin', False):
            return jsonify({'success': False, 'message': '权限不足'}), 403

    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip() or None  # 邮箱可为空
        is_vip = data.get('is_vip', False)
        is_admin = data.get('is_admin', False)
        balance = float(data.get('balance', 0))

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'})

        if db_manager.connect():
            # 检查用户名是否已存在
            existing_user = db_manager.get_user_by_username(username)
            if existing_user:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '用户名已存在'})

            # 创建用户
            hashed_password = hash_password(password)
            user_id = db_manager.create_user(username, hashed_password, email, is_vip, is_admin, balance)

            if user_id and user_id > 0:
                # 保存密码历史记录
                db_manager.save_password_history(user_id, password, hashed_password)
                db_manager.disconnect()
                return jsonify({'success': True, 'message': '用户创建成功'})
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '用户创建失败'})
        else:
            return jsonify({'success': False, 'message': '数据库连接失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'})

# API端点：更新用户信息
@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    """更新用户信息API"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip() or None
            is_vip = data.get('is_vip', False)
            is_admin = data.get('is_admin', False)
            balance = float(data.get('balance', 0))
            new_password = data.get('new_password', '').strip()

            if not username:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '用户名不能为空'})

            # 更新用户基本信息
            update_query = """
            UPDATE users SET username = %s, email = %s, is_vip = %s, is_admin = %s, balance = %s
            WHERE id = %s
            """
            params = (username, email, is_vip, is_admin, balance, user_id)
            result = db_manager.execute_update(update_query, params)

            # 如果提供了新密码，更新密码
            if new_password:
                hashed_password = hash_password(new_password)
                password_query = "UPDATE users SET password = %s WHERE id = %s"
                db_manager.execute_update(password_query, (hashed_password, user_id))

                # 保存密码历史
                db_manager.save_password_history(user_id, new_password, hashed_password)

            if result >= 0:
                db_manager.disconnect()
                return jsonify({'success': True, 'message': '用户信息更新成功'})
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '用户信息更新失败'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'更新失败：{str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# API端点：删除用户
@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """
    删除用户的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        current_user = db_manager.get_user_by_username(session['username'])
        if not current_user or not current_user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 不能删除自己
        if current_user['id'] == user_id:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '不能删除自己的账号'})

        # 删除用户
        success = db_manager.delete_user(user_id)
        db_manager.disconnect()

        if success:
            return jsonify({'success': True, 'message': '用户删除成功'})
        else:
            return jsonify({'success': False, 'message': '用户删除失败'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# ========== 域名管理API ==========

# API端点：获取所有域名
@app.route('/api/admin/domains', methods=['GET'])
def api_get_domains():
    """获取所有域名列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            domains = db_manager.get_all_domains()
            db_manager.disconnect()
            return jsonify({'success': True, 'domains': domains})
        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'获取域名失败：{str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# API端点：创建域名
@app.route('/api/admin/domains', methods=['POST'])
def api_create_domain():
    """创建新域名"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            data = request.get_json()
            domain_name = data.get('domain_name', '').strip()

            if not domain_name:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名不能为空'})

            # 检查域名是否已存在
            existing = db_manager.get_domain_by_name(domain_name)
            if existing:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名已存在'})

            # 创建域名
            domain_id = db_manager.create_domain(domain_name)
            if domain_id > 0:
                db_manager.disconnect()
                return jsonify({'success': True, 'message': '域名创建成功', 'domain_id': domain_id})
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名创建失败'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'创建域名失败：{str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# API端点：更新域名
@app.route('/api/admin/domains/<int:domain_id>', methods=['PUT'])
def api_update_domain(domain_id):
    """更新域名"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            data = request.get_json()
            domain_name = data.get('domain_name', '').strip()

            if not domain_name:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名不能为空'})

            # 检查域名是否已存在（排除当前域名）
            existing = db_manager.get_domain_by_name(domain_name)
            if existing and existing['id'] != domain_id:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名已存在'})

            # 更新域名
            result = db_manager.update_domain(domain_id, domain_name)
            if result:
                db_manager.disconnect()
                return jsonify({'success': True, 'message': '域名更新成功'})
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名更新失败'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'更新域名失败：{str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# API端点：删除域名
@app.route('/api/admin/domains/<int:domain_id>', methods=['DELETE'])
def api_delete_domain(domain_id):
    """删除域名"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            # 检查域名下是否有邮箱
            emails = db_manager.get_emails_by_domain_id(domain_id)
            if emails:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': f'无法删除域名，该域名下还有 {len(emails)} 个邮箱'})

            # 删除域名
            result = db_manager.delete_domain(domain_id)
            if result:
                db_manager.disconnect()
                return jsonify({'success': True, 'message': '域名删除成功'})
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '域名删除失败'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'删除域名失败：{str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# 邮箱注册页面路由
@app.route('/delete_mail/<int:mail_id>', methods=['POST'])
def delete_mail(mail_id):
    """删除单个邮件"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    if not db_manager.connect():
        return jsonify({'success': False, 'message': '数据库连接失败'})

    try:
        # 检查邮件是否存在且用户有权限删除
        # 这里需要检查邮件是否属于用户的邮箱
        user_emails = db_manager.get_user_emails(session['user_id'])
        user_email_addresses = [email['email_address'] for email in user_emails]

        # 获取邮件信息
        mail_info = db_manager.get_email_by_id(mail_id)
        if not mail_info:
            return jsonify({'success': False, 'message': '邮件不存在'})

        # 检查用户是否有权限删除（邮件的收件人是用户的邮箱）
        if mail_info['receiver_email'] not in user_email_addresses:
            return jsonify({'success': False, 'message': '无权限删除此邮件'})

        # 删除邮件
        success = db_manager.delete_email_by_id(mail_id)

        if success:
            db_manager.disconnect()
            return jsonify({'success': True, 'message': '邮件删除成功'})
        else:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '删除失败'})

    except Exception as e:
        db_manager.disconnect()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'})

@app.route('/delete_email/<int:email_id>', methods=['POST'])
def delete_email(email_id):
    """删除邮箱"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    if not db_manager.connect():
        return jsonify({'success': False, 'message': '数据库连接失败'})

    try:
        # 检查邮箱是否属于当前用户
        email_info = db_manager.get_user_email_by_id(email_id, session['user_id'])
        if not email_info:
            return jsonify({'success': False, 'message': '邮箱不存在或无权限删除'})

        # 软删除邮箱（标记为已删除，不实际删除数据）
        success = db_manager.soft_delete_email(email_id)

        if success:
            # 删除该邮箱的所有邮件
            db_manager.delete_emails_by_email_id(email_id)

            db_manager.disconnect()
            return jsonify({'success': True, 'message': '邮箱删除成功'})
        else:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '删除失败'})

    except Exception as e:
        db_manager.disconnect()
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'})

@app.route('/register_email', methods=['GET', 'POST'])
def register_email():
    """
    邮箱注册页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 处理邮箱注册表单提交
        email_prefix = request.form['email_prefix']
        domain_id = request.form['domain_id']
        
        # 构建完整的邮箱地址
        domain_name = None
        if db_manager.connect():
            domains = db_manager.get_all_domains()
            for domain in domains:
                if domain['id'] == int(domain_id):
                    domain_name = domain['domain_name']
                    break
            db_manager.disconnect()
        
        if not domain_name:
            domains = []
            user_emails = []
            user = None
            if db_manager.connect():
                domains = db_manager.get_all_domains()
                user_emails = db_manager.get_user_emails(session['user_id'])
                user = db_manager.get_user_by_username(session['username'])
                db_manager.disconnect()
            return render_template('register_email.html', domains=domains, user_emails=user_emails, user=user, error='无效的域名选择')
        
        email_address = f"{email_prefix}@{domain_name}"

        # 获取用户信息并检查邮箱注册限制
        user = None
        if db_manager.connect():
            user = db_manager.get_user_by_username(session['username'])
            db_manager.disconnect()

        if not user:
            domains = []
            user_emails = []
            if db_manager.connect():
                domains = db_manager.get_all_domains()
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('register_email.html', domains=domains, user_emails=user_emails, user=None, error='用户信息获取失败')

        # 获取当前邮箱数量
        current_email_count = 0
        if db_manager.connect():
            user_emails = db_manager.get_user_emails(session['user_id'])
            current_email_count = len(user_emails)
            db_manager.disconnect()

        # 检查邮箱数量限制和余额
        can_register, error_msg, registration_cost = Config.can_register_email(user, current_email_count)
        if not can_register:
            domains = []
            user_emails = []
            if db_manager.connect():
                domains = db_manager.get_all_domains()
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('register_email.html', domains=domains, user_emails=user_emails, user=user, error=error_msg)

        # 检查邮箱是否已存在（全局检查，不仅仅是当前用户）
        if db_manager.connect():
            # 检查该邮箱是否已被任何用户创建
            if db_manager.check_email_exists(email_address, int(domain_id)):
                db_manager.disconnect()
                domains = []
                user_emails = []
                user = None
                if db_manager.connect():
                    domains = db_manager.get_all_domains()
                    user_emails = db_manager.get_user_emails(session['user_id'])
                    user = db_manager.get_user_by_username(session['username'])
                    db_manager.disconnect()
                return render_template('register_email.html', domains=domains, user_emails=user_emails, user=user, error='该邮箱已被其他用户创建，请选择其他邮箱名')
            db_manager.disconnect()
        
        # 创建新邮箱
        if db_manager.connect():
            # 创建邮箱
            result = db_manager.create_user_email(session['user_id'], email_address, domain_id)
            
            if result > 0:
                # 邮箱创建成功，扣除注册费用（如果需要）
                if registration_cost > 0:
                    current_balance = float(user.get('balance', 0))
                    new_balance = current_balance - registration_cost
                    db_manager.set_user_balance(session['user_id'], new_balance)

                    # 记录消费记录
                    db_manager.add_billing_record(
                        user_id=session['user_id'],
                        amount=registration_cost,
                        type='email_registration',
                        description=f'注册邮箱：{email_address}（第{current_email_count + 1}个）'
                    )

                    print(f"✅ 用户 {user['username']} 注册邮箱 {email_address}，扣费 ¥{registration_cost:.2f}")
                else:
                    print(f"✅ 用户 {user['username']} 免费注册邮箱 {email_address}（第{current_email_count + 1}个）")

                db_manager.disconnect()
                # 注册成功，重定向到邮件列表页面
                return redirect(url_for('mails'))
            elif result == -1:
                db_manager.disconnect()
                # 邮箱已存在
                domains = []
                user_emails = []
                user = None
                if db_manager.connect():
                    domains = db_manager.get_all_domains()
                    user_emails = db_manager.get_user_emails(session['user_id'])
                    user = db_manager.get_user_by_username(session['username'])
                    db_manager.disconnect()
                return render_template('register_email.html', domains=domains, user_emails=user_emails, user=user, error='该邮箱已被其他用户创建，请选择其他邮箱名')
            else:
                db_manager.disconnect()
                # 注册失败，返回错误信息
                domains = []
                user_emails = []
                user = None
                if db_manager.connect():
                    domains = db_manager.get_all_domains()
                    user_emails = db_manager.get_user_emails(session['user_id'])
                    user = db_manager.get_user_by_username(session['username'])
                    db_manager.disconnect()
                return render_template('register_email.html', domains=domains, user_emails=user_emails, user=user, error='邮箱注册失败')
        else:
            domains = []
            user_emails = []
            user = None
            if db_manager.connect():
                domains = db_manager.get_all_domains()
                user_emails = db_manager.get_user_emails(session['user_id'])
                user = db_manager.get_user_by_username(session['username'])
                db_manager.disconnect()
            return render_template('register_email.html', domains=domains, user_emails=user_emails, user=user, error='数据库连接失败')
    
    # GET请求，获取可用域名列表
    domains = []
    if db_manager.connect():
        domains = db_manager.get_all_domains()
        db_manager.disconnect()
    
    # 获取用户信息和已有邮箱
    user = None
    user_emails = []
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    # 渲染邮箱注册页面
    return render_template('register_email.html', domains=domains, user=user, user_emails=user_emails)

# 邮件费用检查函数
def send_email_via_api(from_email, to_email, subject, content):
    """
    通过API发送邮件（旧版本，保持兼容性）
    """
    return send_real_email(from_email, to_email, subject, content)

def send_real_email(from_email, to_email, subject, content):
    """
    真实发送邮件功能 - 使用Resend API
    """
    try:
        print(f"🚀 开始发送验证码邮件: {from_email} -> {to_email}")

        # 使用真实的邮件发送模块
        from email_sender import send_email

        # 调用Resend API发送邮件
        email_result = send_email(
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            content=content
        )

        if email_result:
            print(f"✅ 验证码邮件发送成功！邮件ID: {email_result}")

            # 保存邮件记录到数据库
            if db_manager.connect():
                try:
                    from datetime import datetime

                    # 创建邮件记录
                    email_id = db_manager.save_email(
                        sender_email=from_email,
                        receiver_email=to_email,
                        subject=subject,
                        content=content,
                        sent_time=datetime.now()
                    )

                    # 记录发送日志
                    if email_id:
                        try:
                            query = """
                            INSERT INTO email_send_logs (from_email, to_email, subject, content, type, status, external_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """
                            params = (from_email, to_email, subject, content, 'verification', 'sent', email_result)
                            db_manager.execute_update(query, params)
                        except Exception as log_e:
                            print(f"⚠️ 日志记录失败: {log_e}")

                except Exception as db_e:
                    print(f"⚠️ 数据库记录失败: {db_e}")
                finally:
                    db_manager.disconnect()

            return True
        else:
            print(f"❌ 验证码邮件发送失败")
            return False

    except Exception as e:
        print(f"❌ 验证码邮件发送异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_email_cost_and_deduct(user_id, email_id=None):
    """
    检查邮件费用并扣款（新的VIP计费逻辑）
    返回 (success, message, cost)
    """
    if not db_manager.connect():
        return False, "数据库连接失败", 0

    try:
        # 获取用户信息
        user = db_manager.get_user_by_id(user_id)
        if not user:
            return False, "用户信息获取失败", 0

        # 计算邮件费用
        email_cost, is_vip_free = Config.get_email_send_cost(user)
        current_balance = float(user.get('balance', 0))

        # 检查余额是否足够（免费的不需要检查余额）
        if email_cost > 0 and current_balance < email_cost:
            return False, f'余额不足！当前余额：¥{current_balance:.2f}，需要：¥{email_cost:.2f}', email_cost

        # 扣除费用和更新计数
        if email_cost > 0:
            # 扣除余额
            new_balance = current_balance - email_cost
            db_manager.set_user_balance(user_id, new_balance)

        # 如果是VIP用户，更新VIP邮件计数
        if user.get('is_vip', False):
            db_manager.increment_vip_email_count(user_id)

        # 记录邮件发送记录
        if email_id:
            db_manager.add_email_send_record(user_id, email_id, email_cost, is_vip_free)

        cost_msg = "免费" if email_cost == 0 else f"¥{email_cost:.2f}"
        return True, f'邮件发送成功！费用：{cost_msg}', email_cost

    except Exception as e:
        return False, f"费用检查失败：{str(e)}", 0
    finally:
        db_manager.disconnect()

# 写邮件页面路由
@app.route('/compose', methods=['GET', 'POST'])
def compose():
    """
    写邮件页面视图函数 - 支持附件发送
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 处理邮件发送表单提交
        from_email_id = request.form['from_email_id']
        to_email = request.form['to_email']
        subject = request.form['subject']
        content = request.form['content']
        
        # 获取发送邮箱信息
        from_email_address = None
        if db_manager.connect():
            user_emails = db_manager.get_user_emails(session['user_id'])
            for email in user_emails:
                if email['id'] == int(from_email_id):
                    from_email_address = email['email_address']
                    break
            db_manager.disconnect()
        
        if not from_email_address:
            user_emails = []
            user = None
            if db_manager.connect():
                user = db_manager.get_user_by_username(session['username'])
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('compose.html', user_emails=user_emails, user=user, error='无效的发件邮箱选择')
        
        # 检查用户邮箱容量
        usage = check_user_mailbox_capacity(session['user_id'])
        is_over_limit = usage and usage['total_size_mb'] > 100

        # 处理附件
        attachments = request.files.getlist('attachments')
        attachment_data = []

        # 如果超出容量限制，不允许发送附件
        if is_over_limit and any(att.filename != '' for att in attachments):
            user_emails = []
            user = None
            if db_manager.connect():
                user = db_manager.get_user_by_username(session['username'])
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('compose.html', user_emails=user_emails, user=user,
                                 error=f'邮箱容量已超限（{usage["total_size_mb"]:.2f}MB/100MB），无法发送附件。请先清理邮箱或发送纯文本邮件。')

        # 保存附件到临时目录（仅在容量允许时）
        if not is_over_limit:
            import os
            from werkzeug.utils import secure_filename

            temp_attachments_dir = os.path.join('temp_attachments')
            if not os.path.exists(temp_attachments_dir):
                os.makedirs(temp_attachments_dir)

            for attachment in attachments:
                if attachment.filename != '':
                    filename = secure_filename(attachment.filename)
                    temp_path = os.path.join(temp_attachments_dir, filename)
                    attachment.save(temp_path)

                    # 读取文件内容用于邮件发送
                    with open(temp_path, 'rb') as f:
                        file_content = f.read()

                    attachment_data.append({
                        'filename': filename,
                        'content': file_content,
                        'temp_path': temp_path
                    })
        
        # 发送邮件前先检查费用并扣款
        cost_check_result = check_email_cost_and_deduct(session['user_id'])
        if not cost_check_result[0]:
            # 费用检查失败，清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            user_emails = []
            user = None
            if db_manager.connect():
                user = db_manager.get_user_by_username(session['username'])
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('compose.html', user_emails=user_emails, user=user, error=cost_check_result[1])

        # 使用邮件发送模块发送邮件
        try:
            from email_sender import send_email
            
            # 准备附件数据
            attachments_for_send = []
            if attachment_data:
                for att in attachment_data:
                    attachments_for_send.append({
                        'filename': att['filename'],
                        'content': att['content']
                    })
            
            # 发送邮件
            email_result = send_email(
                from_email=from_email_address,
                to_email=to_email,
                subject=subject,
                content=content,
                attachments=attachments_for_send if attachments_for_send else None
            )
            
            if not email_result:
                raise Exception("邮件发送失败，未返回邮件ID")
            
            # 保存到数据库
            from datetime import datetime
            email_id = None
            if db_manager.connect():
                email_id = db_manager.save_email(from_email_address, to_email, subject, content, datetime.now())
                
                # 保存附件信息到数据库
                if email_id > 0 and attachment_data:
                    # 创建永久附件目录
                    permanent_attachments_dir = os.path.join('sent_attachments', str(email_id))
                    if not os.path.exists(permanent_attachments_dir):
                        os.makedirs(permanent_attachments_dir)
                    
                    for att in attachment_data:
                        # 移动附件到永久目录
                        permanent_path = os.path.join(permanent_attachments_dir, att['filename'])
                        import shutil
                        shutil.move(att['temp_path'], permanent_path)
                        
                        # 保存附件记录到数据库
                        file_size = len(att['content'])
                        db_manager.create_attachment(email_id, att['filename'], permanent_path, file_size)
                        print(f"📎 附件已保存: {att['filename']} ({file_size} 字节)")
                
                db_manager.disconnect()
            
            # 清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            print(f"🎉 邮件发送完成！包含 {len(attachment_data)} 个附件")
            
            # 发送成功，重定向到邮件列表页面
            return redirect(url_for('mails'))
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            # 清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            user_emails = []
            user = None
            if db_manager.connect():
                user = db_manager.get_user_by_username(session['username'])
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('compose.html', user_emails=user_emails, user=user, error=f'邮件发送失败: {str(e)}')
    
    # GET请求，获取用户的邮箱列表
    user_emails = []
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    # 渲染写邮件页面
    return render_template('compose.html', user_emails=user_emails, user=user, error=None)

# 回复邮件路由
@app.route('/compose/reply/<int:mail_id>', methods=['GET', 'POST'])
def compose_reply(mail_id):
    """
    回复邮件页面视图函数 - 支持GET显示和POST发送
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取原邮件信息
    original_mail = None
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if user and user.get('is_vip', False):
            original_mail = db_manager.get_email_by_id(mail_id)
        else:
            original_mail = db_manager.get_user_email_by_id_with_isolation(mail_id, session['user_id'])
        db_manager.disconnect()
    
    if not original_mail:
        return redirect(url_for('mails'))
    
    # 获取用户的邮箱列表
    user_emails = []
    if db_manager.connect():
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    if request.method == 'POST':
        # 处理回复邮件发送（复用compose的逻辑）
        from_email_id = request.form['from_email_id']
        to_email = request.form['to_email']
        subject = request.form['subject']
        content = request.form['content']
        
        # 获取发送邮箱信息
        from_email_address = None
        if db_manager.connect():
            user_emails_temp = db_manager.get_user_emails(session['user_id'])
            for email in user_emails_temp:
                if email['id'] == int(from_email_id):
                    from_email_address = email['email_address']
                    break
            db_manager.disconnect()
        
        if not from_email_address:
            reply_data = {
                'to_email': to_email,
                'subject': subject,
                'content': content
            }
            return render_template('compose.html', user_emails=user_emails, user=user, error='无效的发件邮箱选择', reply_data=reply_data, is_reply=True)
        
        # 处理附件
        attachments = request.files.getlist('attachments')
        attachment_data = []
        
        # 保存附件到临时目录
        import os
        from werkzeug.utils import secure_filename
        
        temp_attachments_dir = os.path.join('temp_attachments')
        if not os.path.exists(temp_attachments_dir):
            os.makedirs(temp_attachments_dir)
        
        for attachment in attachments:
            if attachment.filename != '':
                filename = secure_filename(attachment.filename)
                temp_path = os.path.join(temp_attachments_dir, filename)
                attachment.save(temp_path)
                
                # 读取文件内容用于邮件发送
                with open(temp_path, 'rb') as f:
                    file_content = f.read()
                
                attachment_data.append({
                    'filename': filename,
                    'content': file_content,
                    'temp_path': temp_path
                })
        
        # 发送邮件前先检查费用并扣款
        cost_check_result = check_email_cost_and_deduct(session['user_id'])
        if not cost_check_result[0]:
            # 费用检查失败，清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            user_emails = []
            user = None
            if db_manager.connect():
                user = db_manager.get_user_by_username(session['username'])
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('compose.html', user_emails=user_emails, user=user, error=cost_check_result[1])

        # 使用邮件发送模块发送邮件
        try:
            from email_sender import send_email
            
            # 准备附件数据
            attachments_for_send = []
            if attachment_data:
                for att in attachment_data:
                    attachments_for_send.append({
                        'filename': att['filename'],
                        'content': att['content']
                    })
            
            # 发送邮件
            email_result = send_email(
                from_email=from_email_address,
                to_email=to_email,
                subject=subject,
                content=content,
                attachments=attachments_for_send if attachments_for_send else None
            )
            
            if not email_result:
                raise Exception("邮件发送失败，未返回邮件ID")
            
            # 保存到数据库
            from datetime import datetime
            email_id = None
            if db_manager.connect():
                email_id = db_manager.save_email(from_email_address, to_email, subject, content, datetime.now())
                
                # 保存附件信息到数据库
                if email_id > 0 and attachment_data:
                    # 创建永久附件目录
                    permanent_attachments_dir = os.path.join('sent_attachments', str(email_id))
                    if not os.path.exists(permanent_attachments_dir):
                        os.makedirs(permanent_attachments_dir)
                    
                    for att in attachment_data:
                        # 移动附件到永久目录
                        permanent_path = os.path.join(permanent_attachments_dir, att['filename'])
                        import shutil
                        shutil.move(att['temp_path'], permanent_path)
                        
                        # 保存附件记录到数据库
                        file_size = len(att['content'])
                        db_manager.create_attachment(email_id, att['filename'], permanent_path, file_size)
                
                db_manager.disconnect()
            
            # 清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            # 回复成功，重定向到邮件列表页面
            return redirect(url_for('mails'))
            
        except Exception as e:
            # 清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            reply_data = {
                'to_email': to_email,
                'subject': subject,
                'content': content
            }
            return render_template('compose.html', user_emails=user_emails, user=user, error=f'邮件回复失败: {str(e)}', reply_data=reply_data, is_reply=True)
    
    # GET请求，准备回复邮件的预填信息
    reply_data = {
        'to_email': original_mail.get('sender_email', ''),
        'subject': 'Re: ' + (original_mail.get('subject', '') if not original_mail.get('subject', '').startswith('Re: ') else original_mail.get('subject', '')),
        'content': f"\n\n--- 原邮件 ---\n发件人: {original_mail.get('sender_email', '')}\n收件人: {original_mail.get('receiver_email', '')}\n主题: {original_mail.get('subject', '')}\n时间: {original_mail.get('sent_time', '')}\n\n{original_mail.get('content', '')}"
    }
    
    return render_template('compose.html', user_emails=user_emails, user=user, error=None, reply_data=reply_data, is_reply=True)

# 转发邮件路由
@app.route('/compose/forward/<int:mail_id>', methods=['GET', 'POST'])
def compose_forward(mail_id):
    """
    转发邮件页面视图函数 - 支持GET显示和POST发送
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取原邮件信息
    original_mail = None
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if user and user.get('is_vip', False):
            original_mail = db_manager.get_email_by_id(mail_id)
        else:
            original_mail = db_manager.get_user_email_by_id_with_isolation(mail_id, session['user_id'])
        db_manager.disconnect()
    
    if not original_mail:
        return redirect(url_for('mails'))
    
    # 获取用户的邮箱列表
    user_emails = []
    if db_manager.connect():
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    if request.method == 'POST':
        # 处理转发邮件发送（复用compose的逻辑）
        from_email_id = request.form['from_email_id']
        to_email = request.form['to_email']
        subject = request.form['subject']
        content = request.form['content']
        
        # 获取发送邮箱信息
        from_email_address = None
        if db_manager.connect():
            user_emails_temp = db_manager.get_user_emails(session['user_id'])
            for email in user_emails_temp:
                if email['id'] == int(from_email_id):
                    from_email_address = email['email_address']
                    break
            db_manager.disconnect()
        
        if not from_email_address:
            forward_data = {
                'to_email': to_email,
                'subject': subject,
                'content': content
            }
            return render_template('compose.html', user_emails=user_emails, user=user, error='无效的发件邮箱选择', reply_data=forward_data, is_forward=True)
        
        # 处理附件
        attachments = request.files.getlist('attachments')
        attachment_data = []
        
        # 保存附件到临时目录
        import os
        from werkzeug.utils import secure_filename
        
        temp_attachments_dir = os.path.join('temp_attachments')
        if not os.path.exists(temp_attachments_dir):
            os.makedirs(temp_attachments_dir)
        
        for attachment in attachments:
            if attachment.filename != '':
                filename = secure_filename(attachment.filename)
                temp_path = os.path.join(temp_attachments_dir, filename)
                attachment.save(temp_path)
                
                # 读取文件内容用于邮件发送
                with open(temp_path, 'rb') as f:
                    file_content = f.read()
                
                attachment_data.append({
                    'filename': filename,
                    'content': file_content,
                    'temp_path': temp_path
                })
        
        # 发送邮件前先检查费用并扣款
        cost_check_result = check_email_cost_and_deduct(session['user_id'])
        if not cost_check_result[0]:
            # 费用检查失败，清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            user_emails = []
            user = None
            if db_manager.connect():
                user = db_manager.get_user_by_username(session['username'])
                user_emails = db_manager.get_user_emails(session['user_id'])
                db_manager.disconnect()
            return render_template('compose.html', user_emails=user_emails, user=user, error=cost_check_result[1])

        # 使用邮件发送模块发送邮件
        try:
            from email_sender import send_email
            
            # 准备附件数据
            attachments_for_send = []
            if attachment_data:
                for att in attachment_data:
                    attachments_for_send.append({
                        'filename': att['filename'],
                        'content': att['content']
                    })
            
            # 发送邮件
            email_result = send_email(
                from_email=from_email_address,
                to_email=to_email,
                subject=subject,
                content=content,
                attachments=attachments_for_send if attachments_for_send else None
            )
            
            if not email_result:
                raise Exception("邮件发送失败，未返回邮件ID")
            
            # 保存到数据库
            from datetime import datetime
            email_id = None
            if db_manager.connect():
                email_id = db_manager.save_email(from_email_address, to_email, subject, content, datetime.now())
                
                # 保存附件信息到数据库
                if email_id > 0 and attachment_data:
                    # 创建永久附件目录
                    permanent_attachments_dir = os.path.join('sent_attachments', str(email_id))
                    if not os.path.exists(permanent_attachments_dir):
                        os.makedirs(permanent_attachments_dir)
                    
                    for att in attachment_data:
                        # 移动附件到永久目录
                        permanent_path = os.path.join(permanent_attachments_dir, att['filename'])
                        import shutil
                        shutil.move(att['temp_path'], permanent_path)
                        
                        # 保存附件记录到数据库
                        file_size = len(att['content'])
                        db_manager.create_attachment(email_id, att['filename'], permanent_path, file_size)
                
                db_manager.disconnect()
            
            # 清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            # 转发成功，重定向到邮件列表页面
            return redirect(url_for('mails'))
            
        except Exception as e:
            # 清理临时文件
            for att in attachment_data:
                if os.path.exists(att['temp_path']):
                    os.remove(att['temp_path'])
            
            forward_data = {
                'to_email': to_email,
                'subject': subject,
                'content': content
            }
            return render_template('compose.html', user_emails=user_emails, user=user, error=f'邮件转发失败: {str(e)}', reply_data=forward_data, is_forward=True)
    
    # GET请求，准备转发邮件的预填信息
    forward_data = {
        'to_email': '',
        'subject': 'Fwd: ' + (original_mail.get('subject', '') if not original_mail.get('subject', '').startswith('Fwd: ') else original_mail.get('subject', '')),
        'content': f"--- 转发邮件 ---\n发件人: {original_mail.get('sender_email', '')}\n收件人: {original_mail.get('receiver_email', '')}\n主题: {original_mail.get('subject', '')}\n时间: {original_mail.get('sent_time', '')}\n\n{original_mail.get('content', '')}"
    }
    
    return render_template('compose.html', user_emails=user_emails, user=user, error=None, reply_data=forward_data, is_forward=True)

# 用户信息页面路由
@app.route('/profile')
def profile():
    """
    用户信息页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取用户信息和绑定邮箱
    user = None
    bound_emails = []
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        bound_emails = db_manager.get_bound_emails(session['user_id'])
        db_manager.disconnect()

    # 渲染用户信息页面模板
    return render_template('profile.html', user=user, bound_emails=bound_emails)

# API端点：获取邮件列表
@app.route('/api/mails')
def api_mails():
    """
    获取邮件列表的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 获取邮件列表
    mail_list = []
    if db_manager.connect():
        mail_list = db_manager.get_emails()
        db_manager.disconnect()
    
    return jsonify(mail_list)

# API端点：获取邮件详情
@app.route('/api/mail/<int:mail_id>')
def api_mail_detail(mail_id):
    """
    获取邮件详情的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 获取邮件详情
    mail = {}
    if db_manager.connect():
        mail = db_manager.get_email_by_id(mail_id)
        db_manager.disconnect()
    
    return jsonify(mail)

# API端点：获取所有用户（仅管理员可见）
@app.route('/api/admin/users')
def api_admin_users():
    """
    获取所有用户的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 检查用户是否为管理员
    # 这里需要根据实际需求实现管理员权限检查逻辑
    # 暂时假设所有登录用户都是管理员
    
    # 获取用户列表
    user_list = []
    if db_manager.connect():
        user_list = db_manager.get_all_users()
        db_manager.disconnect()
    
    return jsonify(user_list)









# 附件下载路由
@app.route('/download_attachment/<int:attachment_id>')
def download_attachment(attachment_id):
    """
    下载附件
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取附件信息
    attachment = None
    if db_manager.connect():
        attachment = db_manager.get_attachment_by_id(attachment_id)
        db_manager.disconnect()
    
    if not attachment:
        return "附件不存在", 404
    
    # 检查文件是否存在
    file_path = attachment['file_path']
    
    # 标准化路径，处理各种路径格式
    normalized_path = os.path.normpath(file_path)
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(normalized_path):
        if normalized_path.startswith('./'):
            normalized_path = os.path.join(os.getcwd(), normalized_path[2:])
        else:
            normalized_path = os.path.join(os.getcwd(), normalized_path)
    
    print(f"🔍 附件下载路径: {normalized_path}")
    
    if not os.path.exists(normalized_path):
        # 尝试在received_emails/attachments目录中查找
        alternative_path = os.path.join(os.getcwd(), 'received_emails', 'attachments', attachment['filename'])
        if os.path.exists(alternative_path):
            normalized_path = alternative_path
            print(f"🔍 使用备用路径: {normalized_path}")
        else:
            print(f"❌ 文件不存在: {normalized_path}")
            print(f"❌ 备用路径也不存在: {alternative_path}")
            return "文件不存在", 404
    
    # 发送文件
    from flask import send_file
    return send_file(normalized_path, as_attachment=True, download_name=attachment['filename'])

# 余额充值页面
@app.route('/recharge')
def recharge():
    """余额充值页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = None
    recharge_history = []
    billing_history = []
    email_stats = {}

    if db_manager.connect():
        user = db_manager.get_user_by_id(session['user_id'])
        if user:
            # 检查并更新会员状态
            db_manager.check_and_update_vip_status(session['user_id'])
            # 获取更新后的用户信息
            user = db_manager.get_user_by_id(session['user_id'])
            # 获取充值和消费记录
            recharge_history = db_manager.get_user_recharge_history(session['user_id'])
            billing_history = db_manager.get_user_billing_history(session['user_id'])
            # 获取邮件统计数据
            email_stats = db_manager.get_monthly_email_stats(session['user_id'])
        db_manager.disconnect()

    return render_template('recharge.html',
                         user=user,
                         recharge_history=recharge_history,
                         billing_history=billing_history,
                         email_stats=email_stats)

# 余额充值处理 - 跳转到支付方式选择
@app.route('/recharge_balance', methods=['POST'])
def recharge_balance():
    """处理余额充值 - 跳转到支付方式选择"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    amount = 0
    recharge_type = 'balance'  # 默认是余额充值
    
    # 获取充值金额
    if 'amount' in request.form:
        amount = float(request.form['amount'])
    elif 'custom_amount' in request.form and request.form['custom_amount']:
        amount = float(request.form['custom_amount'])
    elif 'vip_purchase' in request.form:
        amount = 10.0  # VIP费用固定10元
        recharge_type = 'vip'
    
    if amount <= 0 or amount > 1000:
        flash('充值金额必须在1-1000元之间', 'error')
        return redirect(url_for('recharge'))
    
    # 将充值信息保存到session，跳转到支付方式选择页面
    session['pending_payment'] = {
        'amount': amount,
        'type': recharge_type,
        'timestamp': str(datetime.now())
    }
    
    return redirect(url_for('pay_select'))

# 会员购买处理 - 跳转到支付方式选择
@app.route('/purchase_vip', methods=['POST'])
def purchase_vip():
    """处理会员购买 - 直接从余额扣费"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 检查用户余额是否足够
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()

    if not user:
        flash('用户信息获取失败', 'error')
        return redirect(url_for('recharge'))

    # 转换为Decimal类型进行计算
    from decimal import Decimal
    from datetime import datetime, timedelta
    user_balance = Decimal(str(user['balance']))
    vip_cost = Decimal(str(Config.VIP_MONTHLY_COST))

    if user_balance < vip_cost:
        flash(f'余额不足，购买会员需要¥{Config.VIP_MONTHLY_COST}', 'error')
        return redirect(url_for('recharge'))

    # 直接从余额扣费购买会员
    if db_manager.connect():
        try:
            # 开始事务
            db_manager.cursor.execute("START TRANSACTION")

            # 1. 扣除余额
            new_balance = user_balance - vip_cost
            balance_result = db_manager.set_user_balance(session['user_id'], float(new_balance))
            if not balance_result:
                raise Exception("余额更新失败")

            # 2. 设置会员到期时间（续费逻辑）
            if user.get('is_vip', False) and user.get('vip_expire_date'):
                # 已经是VIP，在现有到期时间基础上延长
                current_expire = user['vip_expire_date']
                if isinstance(current_expire, str):
                    from datetime import datetime
                    current_expire = datetime.strptime(current_expire, '%Y-%m-%d %H:%M:%S')

                # 如果当前时间已经超过到期时间，从现在开始计算
                if current_expire < datetime.now():
                    expire_date = datetime.now() + timedelta(days=Config.VIP_DURATION_DAYS)
                else:
                    # 在现有到期时间基础上延长30天
                    expire_date = current_expire + timedelta(days=Config.VIP_DURATION_DAYS)
            else:
                # 新购买VIP，从现在开始计算
                expire_date = datetime.now() + timedelta(days=Config.VIP_DURATION_DAYS)

            # 判断是否为续费（已经是VIP用户）
            is_renewal = user.get('is_vip', False)
            vip_result = db_manager.update_user_vip_status(session['user_id'], True, expire_date, reset_count=not is_renewal)
            if not vip_result:
                raise Exception("VIP状态更新失败")

            # 3. 记录消费记录
            billing_result = db_manager.add_billing_record(
                user_id=session['user_id'],
                amount=float(vip_cost),
                type='vip',
                description=f'购买VIP会员（{Config.VIP_DURATION_DAYS}天）'
            )
            if not billing_result:
                raise Exception("消费记录添加失败")

            # 提交事务
            db_manager.cursor.execute("COMMIT")
            db_manager.disconnect()
            flash('VIP会员购买成功！', 'success')
            return redirect(url_for('recharge'))

        except Exception as e:
            # 回滚事务
            try:
                db_manager.cursor.execute("ROLLBACK")
            except:
                pass
            db_manager.disconnect()
            flash(f'购买失败：{str(e)}', 'error')
            return redirect(url_for('recharge'))

    flash('数据库连接失败', 'error')
    return redirect(url_for('recharge'))

# 验证码发送API
@app.route('/send_verification_code', methods=['POST'])
def send_verification_code():
    """发送验证码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        code_type = data.get('type', 'email_binding')

        if not email:
            return jsonify({'success': False, 'message': '邮箱地址不能为空'})

        # 验证邮箱格式
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})

        if not db_manager.connect():
            return jsonify({'success': False, 'message': '数据库连接失败'})

        # 检查每日发送限制
        can_send, today_count = db_manager.check_verification_code_limit(session['user_id'], email, daily_limit=2)
        if not can_send:
            db_manager.disconnect()
            return jsonify({
                'success': False,
                'message': f'今日验证码发送次数已达上限（{today_count}/2次），请明天再试。这是为了保护有限的邮件发送资源。'
            })

        # 导入必要的模块
        from datetime import datetime, timedelta
        import random

        try:
            # 检查每日发送限制
            can_send, sent_count, daily_limit = db_manager.check_verification_send_limit(
                session['user_id'], email, code_type, daily_limit=2
            )

            if not can_send:
                return jsonify({
                    'success': False,
                    'message': f'今日验证码发送次数已达上限（{sent_count}/{daily_limit}），请明天再试'
                })

            # 删除该用户该邮箱的旧验证码
            db_manager.delete_user_verification_codes(session['user_id'], email, code_type)

            # 生成6位验证码
            code = str(random.randint(100000, 999999))

            # 设置过期时间（10分钟）
            expires_at = datetime.now() + timedelta(minutes=10)

            # 保存验证码
            db_manager.create_verification_code(session['user_id'], email, code, code_type, expires_at)

            # 发送邮件
            try:
                # 使用系统邮箱发送验证码
                from_email = "longgekutta@shiep.edu.kg"
                subject = "邮箱绑定验证码"
                content = f"""
                <html>
                <body>
                    <h2>邮箱绑定验证码</h2>
                    <p>您好！</p>
                    <p>您正在进行邮箱绑定操作，验证码为：</p>
                    <h3 style="color: #007bff; font-size: 24px; letter-spacing: 2px;">{code}</h3>
                    <p>验证码有效期为10分钟，请及时使用。</p>
                    <p>如果这不是您的操作，请忽略此邮件。</p>
                    <br>
                    <p>邮箱监控系统</p>
                </body>
                </html>
                """

                # 调用真实邮件发送功能
                send_success = send_real_email(from_email, email, subject, content)

                if not send_success:
                    return jsonify({'success': False, 'message': '邮件发送失败，请稍后重试'})

                print(f"验证码已发送到 {email}: {code}")

                # 记录验证码发送日志
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
                db_manager.log_verification_code_sent(session['user_id'], email, code_type, client_ip)

            except Exception as e:
                print(f"邮件发送异常: {str(e)}")
                return jsonify({'success': False, 'message': '邮件发送失败，请检查邮箱地址'})

            # 获取剩余发送次数
            stats = db_manager.get_user_verification_code_stats(session['user_id'])
            db_manager.disconnect()

            return jsonify({
                'success': True,
                'message': f'验证码已发送！今日剩余发送次数：{stats["remaining_count"]}/2'
            })

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'发送失败：{str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'请求处理失败：{str(e)}'})

# 验证并绑定邮箱API
@app.route('/verify_and_bind_email', methods=['POST'])
def verify_and_bind_email():
    """验证并绑定邮箱"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()

        if not email or not code:
            return jsonify({'success': False, 'message': '邮箱地址和验证码不能为空'})

        if not db_manager.connect():
            return jsonify({'success': False, 'message': '数据库连接失败'})

        try:
            # 验证验证码
            code_info = db_manager.get_verification_code(session['user_id'], email, code, 'email_binding')

            if not code_info:
                return jsonify({'success': False, 'message': '验证码无效或已过期'})

            # 删除验证码（绑定成功后删除）
            db_manager.delete_verification_code(code_info['id'])

            # 绑定邮箱
            result = db_manager.add_bound_email(session['user_id'], email)

            if result > 0:
                db_manager.disconnect()
                return jsonify({'success': True, 'message': '邮箱绑定成功'})
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '邮箱绑定失败'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'绑定失败：{str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'请求处理失败：{str(e)}'})

# 发送登录验证码API
@app.route('/send_login_verification_code', methods=['POST'])
def send_login_verification_code():
    """发送登录验证码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'success': False, 'message': '邮箱地址不能为空'})

        # 验证邮箱格式
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})

        if not db_manager.connect():
            return jsonify({'success': False, 'message': '数据库连接失败'})

        # 导入必要的模块
        from datetime import datetime, timedelta
        import random

        try:
            # 设置验证码类型
            code_type = 'login'

            # 检查邮箱是否已绑定
            user = db_manager.get_user_by_bound_email(email)
            if not user:
                return jsonify({'success': False, 'message': '该邮箱未绑定任何账户'})

            # 检查每日发送限制
            can_send, today_count = db_manager.check_verification_code_limit(user['id'], email, daily_limit=2)
            if not can_send:
                db_manager.disconnect()
                return jsonify({
                    'success': False,
                    'message': f'今日验证码发送次数已达上限（{today_count}/2次），请明天再试。'
                })

                # 检查60秒间隔
                if limit_info['last_sent_at']:
                    time_diff = datetime.now() - limit_info['last_sent_at']
                    if time_diff.total_seconds() < 60:
                        remaining = 60 - int(time_diff.total_seconds())
                        return jsonify({'success': False, 'message': f'请等待{remaining}秒后再发送'})

            # 删除该邮箱的旧登录验证码
            db_manager.delete_user_verification_codes(None, email, code_type)

            # 生成6位验证码
            code = str(random.randint(100000, 999999))

            # 设置过期时间（10分钟）
            expires_at = datetime.now() + timedelta(minutes=10)

            # 保存验证码
            db_manager.create_verification_code(user['id'], email, code, 'login', expires_at)

            # 更新发送限制
            db_manager.update_verification_limit(user['id'], email, 'login')

            # 发送邮件
            try:
                from_email = "longgekutta@shiep.edu.kg"
                subject = "登录验证码"
                content = f"""
                <html>
                <body>
                    <h2>登录验证码</h2>
                    <p>您好！</p>
                    <p>您正在使用邮箱验证码登录，验证码为：</p>
                    <h3 style="color: #28a745; font-size: 24px; letter-spacing: 2px;">{code}</h3>
                    <p>验证码有效期为10分钟，请及时使用。</p>
                    <p>如果这不是您的操作，请忽略此邮件。</p>
                    <br>
                    <p>邮箱监控系统</p>
                </body>
                </html>
                """

                send_success = send_email_via_api(from_email, email, subject, content)

                if not send_success:
                    return jsonify({'success': False, 'message': '邮件发送失败，请稍后重试'})

                print(f"登录验证码已发送到 {email}: {code}")

                # 记录验证码发送日志
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
                db_manager.log_verification_code_sent(user['id'], email, code_type, client_ip)

            except Exception as e:
                print(f"邮件发送异常: {str(e)}")
                return jsonify({'success': False, 'message': '邮件发送失败，请检查邮箱地址'})

            # 获取剩余发送次数
            stats = db_manager.get_user_verification_code_stats(user['id'])
            db_manager.disconnect()

            return jsonify({
                'success': True,
                'message': f'验证码已发送！今日剩余发送次数：{stats["remaining_count"]}/2'
            })

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'发送失败：{str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'请求处理失败：{str(e)}'})

# 邮箱验证码登录API
@app.route('/email_login', methods=['POST'])
def email_login():
    """邮箱验证码登录"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()

        if not email or not code:
            return jsonify({'success': False, 'message': '邮箱地址和验证码不能为空'})

        if not db_manager.connect():
            return jsonify({'success': False, 'message': '数据库连接失败'})

        try:
            # 检查邮箱是否已绑定
            user = db_manager.get_user_by_bound_email(email)
            if not user:
                return jsonify({'success': False, 'message': '该邮箱未绑定任何账户'})

            # 验证验证码
            code_info = db_manager.get_verification_code(user['id'], email, code, 'login')

            if not code_info:
                return jsonify({'success': False, 'message': '验证码无效或已过期'})

            # 标记验证码为已使用
            db_manager.use_verification_code(code_info['id'])

            # 设置session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email_login'] = True  # 标记为邮箱登录

            db_manager.disconnect()
            return jsonify({
                'success': True,
                'message': '登录成功',
                'need_password_reset': True  # 邮箱登录后需要重置密码
            })

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'登录失败：{str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'请求处理失败：{str(e)}'})

# 邮箱登录后密码重置页面
@app.route('/reset_password_after_email_login', methods=['GET', 'POST'])
def reset_password_after_email_login():
    """邮箱登录后的密码重置"""
    if 'user_id' not in session or not session.get('email_login'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            return render_template('reset_password_after_email_login.html',
                                 error='请填写完整的密码信息')

        if new_password != confirm_password:
            return render_template('reset_password_after_email_login.html',
                                 error='两次输入的密码不一致')

        if len(new_password) < 6:
            return render_template('reset_password_after_email_login.html',
                                 error='密码长度至少6位')

        # 更新密码
        if db_manager.connect():
            try:
                # 加密新密码（使用统一哈希函数）
                hashed_password = hash_password(new_password)

                # 更新密码
                success = db_manager.update_user_password(session['user_id'], hashed_password)

                if success:
                    # 清除邮箱登录标记
                    session.pop('email_login', None)
                    db_manager.disconnect()
                    flash(f'密码设置成功！您的新密码是：{new_password}', 'success')
                    return redirect(url_for('index'))
                else:
                    db_manager.disconnect()
                    return render_template('reset_password_after_email_login.html',
                                         error='密码更新失败')

            except Exception as e:
                db_manager.disconnect()
                return render_template('reset_password_after_email_login.html',
                                     error=f'密码更新失败：{str(e)}')
        else:
            return render_template('reset_password_after_email_login.html',
                                 error='数据库连接失败')

    return render_template('reset_password_after_email_login.html')

# 修改密码API
@app.route('/change_password', methods=['POST'])
def change_password():
    """修改密码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})

    try:
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()

        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': '请填写完整的密码信息'})

        if new_password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的新密码不一致'})

        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度至少6位'})

        if not db_manager.connect():
            return jsonify({'success': False, 'message': '数据库连接失败'})

        try:
            # 获取用户信息验证当前密码
            user = db_manager.get_user_by_username(session['username'])
            if not user:
                return jsonify({'success': False, 'message': '用户信息获取失败'})

            # 验证当前密码（使用统一验证函数）
            if not verify_password(current_password, user['password'], user['id']):
                return jsonify({'success': False, 'message': '当前密码不正确'})

            # 加密新密码（使用统一哈希函数）
            new_password_hash = hash_password(new_password)

            # 更新密码
            success = db_manager.update_user_password(session['user_id'], new_password_hash)

            if success:
                # 保存密码历史记录
                db_manager.save_password_history(session['user_id'], new_password, new_password_hash)
                db_manager.disconnect()
                return jsonify({
                    'success': True,
                    'message': f'密码修改成功！您的新密码是：{new_password}',
                    'new_password': new_password
                })
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '密码修改失败'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'密码修改失败：{str(e)}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'请求处理失败：{str(e)}'})

# 支付方式选择页面
@app.route('/pay_select')
def pay_select():
    """支付方式选择页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查是否有待支付订单
    pending_payment = session.get('pending_payment')
    if not pending_payment:
        flash('无效的支付请求', 'error')
        return redirect(url_for('recharge'))
    
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    return render_template('pay_select.html', user=user, payment=pending_payment)

# 支付确认页面 - 易支付集成
@app.route('/pay_confirm/<payment_method>')
def pay_confirm(payment_method):
    """支付确认页面 - 易支付集成版本"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查是否有待支付订单
    pending_payment = session.get('pending_payment')
    if not pending_payment:
        flash('无效的支付请求', 'error')
        return redirect(url_for('recharge'))
    
    # 验证支付方式 - 目前只支持支付宝
    if payment_method not in ['alipay']:
        flash('当前只支持支付宝支付', 'error')
        return redirect(url_for('pay_select'))

    # 额外检查：如果有人直接访问微信支付URL，重定向到支付宝
    if payment_method == 'wechat':
        flash('微信支付暂时不可用，已为您切换到支付宝支付', 'info')
        return redirect(url_for('pay_confirm', payment_method='alipay'))
    
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 生成订单号
    order_id = YiPayUtil.generate_order_no()

    # 保存订单号到session
    session['pending_payment']['order_id'] = order_id
    session['pending_payment']['method'] = payment_method

    print(f"🚀 生成支付订单:")
    print(f"   支付类型: {payment_method}")
    print(f"   订单号: {order_id}")
    print(f"   金额: ¥{pending_payment['amount']:.2f}")
    print(f"   用户: {session['user_id']}")

    # 渲染支付确认页面
    return render_template('pay_confirm.html',
                         user=user,
                         payment=pending_payment,
                         payment_method=payment_method,
                         order_id=order_id)

# 易支付异步通知处理
@app.route('/payment/notify', methods=['POST', 'GET'])
def yipay_notify():
    """易支付异步通知处理"""
    try:
        # 获取通知参数（支持GET和POST）
        if request.method == 'POST':
            params = request.form.to_dict()
        else:
            params = request.args.to_dict()
        
        print(f"💰 收到易支付通知: {params}")
        
        # 验证必要参数
        required_params = ['pid', 'trade_no', 'out_trade_no', 'type', 'name', 'money', 'trade_status', 'sign']
        for param in required_params:
            if param not in params:
                print(f"❌ 缺少必要参数: {param}")
                return "fail", 400
        
        # 验证商户PID
        if params['pid'] != YIPAY_PID:
            print(f"❌ 商户PID不匹配: {params['pid']} != {YIPAY_PID}")
            return "fail", 400
        
        # 验签
        if not YiPayUtil.verify_sign(params, YIPAY_KEY):
            print("❌ 签名验证失败")
            return "fail", 400
        
        # 检查支付状态
        if params['trade_status'] != 'TRADE_SUCCESS':
            print(f"❌ 支付未成功: {params['trade_status']}")
            return "fail", 400
        
        # 处理支付成功逻辑
        order_no = params['out_trade_no']
        amount = float(params['money'])
        payment_type = params['type']  # alipay, wxpay等
        trade_no = params['trade_no']  # 易支付平台订单号
        param = params.get('param', '')  # 业务参数
        
        print(f"✅ 支付成功:")
        print(f"   订单号: {order_no}")
        print(f"   金额: ¥{amount}")
        print(f"   支付方式: {payment_type}")
        print(f"   平台订单号: {trade_no}")
        print(f"   业务参数: {param}")
        
        # 解析业务参数
        user_id = None
        charge_type = None
        if param:
            try:
                param_parts = param.split(',')
                for part in param_parts:
                    if part.startswith('user_id:'):
                        user_id = int(part.split(':')[1])
                    elif part.startswith('type:'):
                        charge_type = part.split(':')[1]
            except:
                print("⚠️ 解析业务参数失败")
        
        if not user_id or not charge_type:
            print("❌ 无法获取用户ID或充值类型")
            return "fail", 400
        
        # 执行充值逻辑
        success = process_yipay_payment(user_id, order_no, amount, payment_type, charge_type, trade_no)
        
        if success:
            print("✅ 充值处理成功")
            return "success"
        else:
            print("❌ 充值处理失败")
            return "fail", 500
            
    except Exception as e:
        print(f"❌ 处理易支付通知异常: {str(e)}")
        return "fail", 500

# 易支付同步回调处理
@app.route('/payment/return', methods=['GET'])
def yipay_return():
    """易支付同步回调处理（页面跳转）"""
    try:
        params = request.args.to_dict()
        print(f"🔄 收到易支付同步回调: {params}")
        
        # 基本验证
        if 'out_trade_no' in params and 'trade_status' in params:
            if params['trade_status'] == 'TRADE_SUCCESS':
                flash('支付成功！正在为您充值...', 'success')
            else:
                flash('支付失败，请重试', 'error')
        else:
            flash('支付结果未知，请稍后查看账户余额', 'info')
        
        # 清除session中的待支付订单
        if 'pending_payment' in session:
            del session['pending_payment']
        
        return redirect(url_for('recharge'))
        
    except Exception as e:
        print(f"❌ 处理同步回调异常: {str(e)}")
        flash('支付处理异常，请联系客服', 'error')
        return redirect(url_for('recharge'))

def process_yipay_payment(user_id, order_no, amount, payment_type, charge_type, trade_no):
    """处理易支付成功的支付"""
    try:
        if not db_manager.connect():
            return False
        
        # 检查订单是否已处理（防止重复处理）
        check_query = "SELECT COUNT(*) as count FROM recharge_records WHERE description LIKE %s"
        check_params = (f"%{order_no}%",)
        existing = db_manager.execute_query(check_query, check_params)
        
        if existing and existing[0]['count'] > 0:
            print(f"⚠️ 订单 {order_no} 已处理，跳过重复处理")
            db_manager.disconnect()
            return True
        
        # 根据充值类型处理
        if charge_type == 'balance':
            # 余额充值
            success = db_manager.update_user_balance(user_id, amount)
            if success:
                description = f"易支付余额充值¥{amount:.2f}（{payment_type}，订单号:{order_no}，平台单号:{trade_no}）"
                db_manager.add_recharge_record(user_id, 'balance', amount, description)
                print(f"✅ 用户 {user_id} 余额充值成功: +¥{amount:.2f}")
                return True
                
        elif charge_type == 'vip':
            # 会员购买
            from datetime import timedelta
            expire_date = datetime.now() + timedelta(days=30)
            success = db_manager.set_user_vip(user_id, expire_date)
            
            if success:
                description = f"易支付会员购买¥{amount:.2f}（{payment_type}，订单号:{order_no}，平台单号:{trade_no}）"
                db_manager.add_recharge_record(user_id, 'vip', amount, description)
                print(f"✅ 用户 {user_id} 会员开通成功，有效期至: {expire_date}")
                return True
        
        db_manager.disconnect()
        return False
        
    except Exception as e:
        print(f"❌ 处理支付异常: {str(e)}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.disconnect()
        return False

# 支付完成确认
@app.route('/pay_complete', methods=['POST'])
def pay_complete():
    """支付完成确认 - 支持混合支付方式"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查是否有待支付订单
    pending_payment = session.get('pending_payment')
    if not pending_payment:
        flash('无效的支付请求', 'error')
        return redirect(url_for('recharge'))
    
    user_id = session['user_id']
    amount = pending_payment['amount']
    payment_type = pending_payment['type']
    original_method = pending_payment.get('method', 'unknown')  
    order_id = pending_payment.get('order_id', '')
    
    # 获取用户实际选择的支付方式
    selected_method = request.form.get('selected_payment_method', 'alipay')
    
    # 处理支付截图上传（可选）
    payment_screenshot = None
    screenshot_filename = None
    if 'payment_screenshot' in request.files:
        screenshot = request.files['payment_screenshot']
        if screenshot.filename != '':
            from werkzeug.utils import secure_filename
            screenshot_filename = f"{order_id}_{secure_filename(screenshot.filename)}"
            screenshot_path = os.path.join('payment_screenshots', screenshot_filename)
            
            # 创建截图保存目录
            if not os.path.exists('payment_screenshots'):
                os.makedirs('payment_screenshots')
            
            screenshot.save(screenshot_path)
            payment_screenshot = screenshot_path
    
    if db_manager.connect():
        try:
            if selected_method == 'alipay':
                # 支付宝支付 - 标记为等待自动确认
                success = create_pending_payment_record(
                    user_id, order_id, amount, payment_type, 
                    'alipay', 'waiting_auto', payment_screenshot, screenshot_filename
                )
                if success:
                    flash('支付提交成功！支付宝用户1-3分钟内自动充值', 'success')
                else:
                    flash('提交失败，请重试', 'error')
                    
            elif selected_method == 'wechat':
                # 微信支付 - 标记为等待人工确认
                success = create_pending_payment_record(
                    user_id, order_id, amount, payment_type,
                    'wechat', 'waiting_manual', payment_screenshot, screenshot_filename
                )
                if success:
                    flash('支付提交成功！我们会尽快为您手动充值', 'info')
                else:
                    flash('提交失败，请重试', 'error')
                    
        except Exception as e:
            flash(f'处理支付时出错: {str(e)}', 'error')
        finally:
            db_manager.disconnect()
    
    # 清除待支付订单
    if 'pending_payment' in session:
        del session['pending_payment']
    
    return redirect(url_for('recharge'))

def create_pending_payment_record(user_id, order_id, amount, payment_type, 
                                 method, status, screenshot_path, screenshot_filename):
    """创建待确认支付记录"""
    try:
        # 准备记录数据
        record_data = {
            'user_id': user_id,
            'order_id': order_id,
            'amount': amount,
            'payment_type': payment_type,  # 'balance' 或 'vip'
            'payment_method': method,      # 'alipay' 或 'wechat'
            'status': status,              # 'waiting_auto', 'waiting_manual', 'confirmed', 'cancelled'
            'screenshot_path': screenshot_path,
            'screenshot_filename': screenshot_filename,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # 插入数据库 (需要先创建相应的数据库表)
        success = db_manager.create_pending_payment(record_data)
        return success
        
    except Exception as e:
        print(f"❌ 创建待确认支付记录失败: {e}")
        return False

# 二维码图片路由 - 商户收款码
@app.route('/wx-bissness-pay.png')
def wechat_qr():
    """微信支付二维码 - 商户收款码"""
    return send_file('wx-bissness-pay.png')

@app.route('/zfb-bissness-pay.jpg')
def alipay_qr():
    """支付宝二维码 - 商户收款码"""
    return send_file('zfb-bissness-pay.jpg')

# 管理员待确认支付页面
@app.route('/admin/pending_payments')
def admin_pending_payments():
    """管理员待确认支付页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 检查管理员权限
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user.get('is_vip', False):
        return "权限不足", 403
    
    # 获取状态筛选
    status_filter = request.args.get('status', 'waiting_manual')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # 获取待确认支付列表
    pending_payments = []
    total_count = 0
    if db_manager.connect():
        pending_payments = db_manager.get_pending_payments(status_filter, per_page, offset)
        total_count = db_manager.get_pending_payments_count(status_filter)
        db_manager.disconnect()
    
    # 计算分页信息
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    return render_template('admin_pending_payments.html',
                         pending_payments=pending_payments,
                         user=user,
                         status_filter=status_filter,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         prev_page=prev_page,
                         next_page=next_page,
                         total_count=total_count)

# 确认支付API
@app.route('/admin/confirm_payment/<int:payment_id>', methods=['POST'])
def admin_confirm_payment(payment_id):
    """管理员确认支付"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未授权'})
    
    # 检查管理员权限
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
    
    if not user or not user.get('is_vip', False):
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.disconnect()
        return jsonify({'success': False, 'message': '权限不足'})
    
    # 获取管理员备注
    admin_note = request.json.get('admin_note', '') if request.is_json else request.form.get('admin_note', '')
    
    # 确认支付
    success, message = db_manager.confirm_pending_payment(payment_id, session['user_id'], admin_note)
    
    if db_manager.connection and db_manager.connection.is_connected():
        db_manager.disconnect()
    
    return jsonify({'success': success, 'message': message})

# 取消支付API  
@app.route('/admin/cancel_payment/<int:payment_id>', methods=['POST'])
def admin_cancel_payment(payment_id):
    """管理员取消支付"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未授权'})
    
    # 检查管理员权限
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
    
    if not user or not user.get('is_vip', False):
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.disconnect()
        return jsonify({'success': False, 'message': '权限不足'})
    
    # 获取管理员备注
    admin_note = request.json.get('admin_note', '') if request.is_json else request.form.get('admin_note', '')
    
    # 取消支付
    success, message = db_manager.cancel_pending_payment(payment_id, session['user_id'], admin_note)
    
    if db_manager.connection and db_manager.connection.is_connected():
        db_manager.disconnect()
    
    return jsonify({'success': success, 'message': message})

# 支付监控API
@app.route('/api/payment_notify', methods=['POST'])
def api_payment_notify():
    """接收支付监控系统的通知"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        amount = float(data.get('amount', 0))
        payment_info = data.get('payment_info', {})
        source = data.get('source', 'unknown')
        
        print(f"💰 收到支付通知: 订单{order_id}, 金额¥{amount}, 来源{source}")
        
        if not order_id or amount <= 0:
            return jsonify({'success': False, 'message': '无效的支付信息'}), 400
        
        # 处理支付（这里需要根据您的订单系统实现）
        success = process_auto_payment(order_id, amount, payment_info)
        
        if success:
            return jsonify({'success': True, 'message': '处理成功'})
        else:
            return jsonify({'success': False, 'message': '处理失败'}), 500
            
    except Exception as e:
        print(f"❌ 处理支付通知失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def process_auto_payment(order_id, amount, payment_info):
    """处理自动支付 - 支付宝邮件通知触发"""
    try:
        print(f"🔍 处理自动支付: 订单{order_id}, 金额¥{amount}")

        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return False

        try:
            # 查找匹配的待支付订单
            query = """
            SELECT * FROM pending_payments
            WHERE order_id = %s AND status = 'waiting_auto' AND payment_method = 'alipay'
            ORDER BY created_at DESC LIMIT 1
            """
            pending_orders = db_manager.execute_query(query, (order_id,))

            if not pending_orders:
                print(f"⚠️ 未找到匹配的待支付订单: {order_id}")
                # 尝试按金额匹配最近的订单
                query = """
                SELECT * FROM pending_payments
                WHERE amount = %s AND status = 'waiting_auto' AND payment_method = 'alipay'
                AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY created_at DESC LIMIT 1
                """
                pending_orders = db_manager.execute_query(query, (amount,))

                if not pending_orders:
                    print(f"⚠️ 也未找到匹配金额的订单: ¥{amount}")
                    return False
                else:
                    print(f"✅ 按金额匹配到订单: {pending_orders[0]['order_id']}")

            pending_order = pending_orders[0]
            user_id = pending_order['user_id']
            payment_type = pending_order['payment_type']  # 'balance' 或 'vip'

            print(f"📋 匹配订单信息: 用户{user_id}, 类型{payment_type}, 金额¥{amount}")

            # 执行充值逻辑
            if payment_type == 'balance':
                # 余额充值
                success = db_manager.update_user_balance(user_id, amount)
                if success:
                    description = f"支付宝自动充值¥{amount:.2f}（订单号:{order_id}）"
                    db_manager.add_recharge_record(user_id, 'balance', amount, description)
                    print(f"✅ 用户 {user_id} 余额充值成功: +¥{amount:.2f}")

            elif payment_type == 'vip':
                # 会员购买
                from datetime import timedelta
                expire_date = datetime.now() + timedelta(days=30)
                success = db_manager.set_user_vip(user_id, expire_date)
                if success:
                    description = f"支付宝自动开通会员¥{amount:.2f}（订单号:{order_id}）"
                    db_manager.add_recharge_record(user_id, 'vip', amount, description)
                    print(f"✅ 用户 {user_id} 会员开通成功，有效期至: {expire_date}")
            else:
                print(f"❌ 未知的支付类型: {payment_type}")
                return False

            if success:
                # 更新待支付订单状态为已确认
                update_query = """
                UPDATE pending_payments
                SET status = 'confirmed',
                    admin_note = '支付宝邮件自动确认',
                    updated_at = NOW()
                WHERE id = %s
                """
                db_manager.execute_update(update_query, (pending_order['id'],))
                print(f"✅ 订单状态已更新为已确认")
                return True
            else:
                print(f"❌ 充值处理失败")
                return False

        finally:
            db_manager.disconnect()

    except Exception as e:
        print(f"❌ 自动支付处理失败: {e}")
        if db_manager.connection and db_manager.connection.is_connected():
            db_manager.disconnect()
        return False

# 自动支付处理函数已整合到 process_auto_payment 中

# 管理员邮件管理页面路由
@app.route('/admin/emails')
def admin_emails():
    """管理员邮件管理页面"""
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 检查管理员权限
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()

    if not user or not user.get('is_admin', False):
        return "权限不足", 403

    # 获取过滤参数
    filter_type = request.args.get('filter_type', 'all')
    search_keyword = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    # 获取邮件列表
    emails_list = []
    total_count = 0
    if db_manager.connect():
        if filter_type == 'admin':
            # 只显示该管理员创建的邮箱的邮件
            emails_list = db_manager.get_admin_created_emails(user['id'], per_page, offset, search_keyword)
            total_count = db_manager.get_admin_created_emails_count(user['id'], search_keyword)
        else:
            # 显示所有邮件
            emails_list = db_manager.get_all_emails_for_admin(per_page, offset, search_keyword)
            total_count = db_manager.get_all_emails_count_for_admin(search_keyword)
        db_manager.disconnect()

    # 计算分页信息
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None

    return render_template('admin_emails.html',
                         emails=emails_list,
                         user=user,
                         filter_type=filter_type,
                         search_keyword=search_keyword,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         prev_page=prev_page,
                         next_page=next_page,
                         total_count=total_count)

# 管理员删除邮件API
@app.route('/api/admin/emails/<int:email_id>/delete', methods=['POST'])
def api_delete_email(email_id):
    """删除邮件API"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 删除邮件
        success = db_manager.delete_email(email_id)
        db_manager.disconnect()

        if success:
            return jsonify({'success': True, 'message': '邮件删除成功'})
        else:
            return jsonify({'success': False, 'message': '邮件删除失败'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# ========== 充值码管理API ==========

# 获取未使用的注册码API
@app.route('/api/admin/unused_registration_codes')
def api_get_unused_registration_codes():
    """获取所有未使用的注册码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 获取未使用的注册码
        codes = db_manager.get_unused_registration_codes()
        db_manager.disconnect()

        return jsonify({'success': True, 'codes': codes})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# 获取未使用的充值码API
@app.route('/api/admin/unused_recharge_codes/<float:amount>')
def api_get_unused_recharge_codes(amount):
    """获取指定面额的未使用充值码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 获取未使用的充值码
        codes = db_manager.get_unused_recharge_codes_by_amount(amount)
        db_manager.disconnect()

        return jsonify({'success': True, 'codes': codes})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# 生成充值码API
@app.route('/api/admin/generate_recharge_codes', methods=['POST'])
def api_generate_recharge_codes():
    """生成充值码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            data = request.get_json()
            amount = float(data.get('amount', 0))
            count = int(data.get('count', 1))
            description = data.get('description', f'¥{amount}充值码')

            if amount <= 0 or count <= 0:
                return jsonify({'success': False, 'message': '参数无效'})

            if count > 500:
                return jsonify({'success': False, 'message': '一次最多只能生成500个充值码'})

            # 生成充值码
            import random
            import string
            generated_codes = []

            for i in range(count):
                # 生成唯一的充值码
                while True:
                    code = f'RC{amount:g}' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    # 检查是否已存在
                    existing = db_manager.get_recharge_code_by_code(code)
                    if not existing:
                        break

                # 创建充值码
                result = db_manager.create_recharge_code(code, amount, description, user['id'])
                if result > 0:
                    generated_codes.append(code)

            db_manager.disconnect()

            if len(generated_codes) == count:
                return jsonify({'success': True, 'message': f'成功生成 {count} 个充值码', 'codes': generated_codes})
            else:
                return jsonify({'success': False, 'message': f'只成功生成 {len(generated_codes)} 个充值码'})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# 获取充值码列表API
@app.route('/api/admin/recharge_codes')
def api_get_recharge_codes():
    """获取充值码列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        try:
            page = int(request.args.get('page', 1))
            per_page = 20
            offset = (page - 1) * per_page
            amount_filter = request.args.get('amount')
            amount_filter = float(amount_filter) if amount_filter else None

            # 获取充值码列表
            codes = db_manager.get_recharge_codes(per_page, offset, amount_filter)
            total_count = db_manager.get_recharge_codes_count(amount_filter)

            # 计算分页信息
            total_pages = (total_count + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages

            pagination = {
                'page': page,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'total_count': total_count
            }

            db_manager.disconnect()

            return jsonify({'success': True, 'codes': codes, 'pagination': pagination})

        except Exception as e:
            db_manager.disconnect()
            return jsonify({'success': False, 'message': f'获取失败: {str(e)}'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# 删除充值码API
@app.route('/api/admin/recharge_codes/<code>/delete', methods=['POST'])
def api_delete_recharge_code(code):
    """删除充值码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 删除充值码
        result = db_manager.delete_recharge_code(code)
        db_manager.disconnect()

        if result > 0:
            return jsonify({'success': True, 'message': '充值码删除成功'})
        else:
            return jsonify({'success': False, 'message': '充值码删除失败'})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# 批量删除已使用充值码API
@app.route('/api/admin/recharge_codes/delete_used', methods=['POST'])
def api_delete_used_recharge_codes():
    """批量删除已使用的充值码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 批量删除已使用的充值码
        deleted_count = db_manager.delete_used_recharge_codes()
        db_manager.disconnect()

        return jsonify({'success': True, 'message': f'成功删除 {deleted_count} 个已使用的充值码', 'deleted_count': deleted_count})
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

# ========== 咸鱼链接管理和充值码兑换 ==========

# 咸鱼链接配置（管理员可配置）
XIANYU_LINKS = {
    1: "https://m.tb.cn/h.g123456?tk=ABC123",    # ¥1充值码链接
    5: "https://m.tb.cn/h.g234567?tk=DEF456",    # ¥5充值码链接
    10: "https://m.tb.cn/h.g345678?tk=GHI789",   # ¥10充值码链接
    20: "https://m.tb.cn/h.g456789?tk=JKL012"    # ¥20充值码链接
}

# 获取咸鱼购买链接API
@app.route('/api/xianyu_link/<int:amount>')
def api_get_xianyu_link(amount):
    """获取指定金额的咸鱼购买链接"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    if amount in XIANYU_LINKS:
        return jsonify({'success': True, 'link': XIANYU_LINKS[amount]})
    else:
        return jsonify({'success': False, 'message': '暂不支持该金额的充值'})

# 充值码兑换API
@app.route('/api/redeem_code', methods=['POST'])
def api_redeem_code():
    """兑换充值码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()

        if not code:
            return jsonify({'success': False, 'message': '请输入充值码'})

        if db_manager.connect():
            # 查找充值码
            recharge_code = db_manager.get_recharge_code_by_code(code)

            if not recharge_code:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '充值码不存在'})

            if recharge_code['is_used']:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '充值码已被使用'})

            # 使用充值码
            use_result = db_manager.use_recharge_code(code, session['user_id'])

            if use_result > 0:
                # 获取用户当前余额
                user = db_manager.get_user_by_id(session['user_id'])
                current_balance = float(user.get('balance', 0))
                new_balance = current_balance + float(recharge_code['amount'])

                # 更新用户余额
                db_manager.set_user_balance(session['user_id'], new_balance)

                # 记录充值记录
                db_manager.add_billing_record(
                    user_id=session['user_id'],
                    amount=float(recharge_code['amount']),
                    type='recharge_code',
                    description=f'充值码兑换：{code}'
                )

                db_manager.disconnect()

                print(f"✅ 用户 {user['username']} 使用充值码 {code} 充值 ¥{recharge_code['amount']}")

                return jsonify({
                    'success': True,
                    'message': '充值成功',
                    'amount': float(recharge_code['amount']),
                    'new_balance': new_balance
                })
            else:
                db_manager.disconnect()
                return jsonify({'success': False, 'message': '充值码使用失败'})
        else:
            return jsonify({'success': False, 'message': '数据库连接失败'})

    except Exception as e:
        if db_manager.connection:
            db_manager.disconnect()
        return jsonify({'success': False, 'message': f'兑换失败: {str(e)}'})

# 管理员配置咸鱼链接API
@app.route('/api/admin/xianyu_links', methods=['GET', 'POST'])
def api_admin_xianyu_links():
    """管理员配置咸鱼链接"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403
        db_manager.disconnect()
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'})

    if request.method == 'GET':
        # 获取当前配置的链接
        return jsonify({'success': True, 'links': XIANYU_LINKS})

    elif request.method == 'POST':
        # 更新链接配置
        try:
            data = request.get_json()
            amount = int(data.get('amount'))
            link = data.get('link', '').strip()

            if amount in [1, 5, 10, 20] and link:
                XIANYU_LINKS[amount] = link
                return jsonify({'success': True, 'message': f'¥{amount} 充值链接更新成功'})
            else:
                return jsonify({'success': False, 'message': '参数无效'})

        except Exception as e:
            return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# ========== 邮箱容量管理功能 ==========

def check_user_mailbox_capacity(user_id):
    """检查用户邮箱容量"""
    if db_manager.connect():
        usage = db_manager.get_user_mailbox_usage(user_id)
        db_manager.disconnect()
        return usage
    return None

def cleanup_user_mailbox_if_needed(user_id):
    """如果需要，清理用户邮箱"""
    if db_manager.connect():
        usage = db_manager.get_user_mailbox_usage(user_id)
        if usage['total_size_mb'] > 100:
            deleted_count = db_manager.cleanup_user_mailbox(user_id, 100)
            db_manager.disconnect()
            return deleted_count
        db_manager.disconnect()
    return 0

# API端点：获取用户邮箱使用情况
@app.route('/api/mailbox_usage')
def api_get_mailbox_usage():
    """获取当前用户邮箱使用情况"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    usage = check_user_mailbox_capacity(session['user_id'])
    if usage:
        # 检查是否超出限制
        is_over_limit = usage['total_size_mb'] > 100

        return jsonify({
            'success': True,
            'usage': usage,
            'limit_mb': 100,
            'is_over_limit': is_over_limit,
            'usage_percentage': min(100, (usage['total_size_mb'] / 100) * 100)
        })
    else:
        return jsonify({'success': False, 'message': '获取使用情况失败'}), 500

# API端点：手动清理邮箱
@app.route('/api/cleanup_mailbox', methods=['POST'])
def api_cleanup_mailbox():
    """手动清理用户邮箱"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    deleted_count = cleanup_user_mailbox_if_needed(session['user_id'])

    if deleted_count > 0:
        return jsonify({
            'success': True,
            'message': f'已清理 {deleted_count} 封旧邮件',
            'deleted_count': deleted_count
        })
    else:
        return jsonify({
            'success': True,
            'message': '邮箱容量正常，无需清理',
            'deleted_count': 0
        })

# 定时清理任务（可以通过cron或其他方式调用）
@app.route('/api/admin/cleanup_all_mailboxes', methods=['POST'])
def api_cleanup_all_mailboxes():
    """管理员清理所有超限邮箱"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    # 检查管理员权限
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        if not user or not user.get('is_admin', False):
            db_manager.disconnect()
            return jsonify({'success': False, 'message': '权限不足'}), 403

        # 获取所有用户
        all_users = db_manager.get_all_users()
        cleaned_users = []

        for user in all_users:
            usage = db_manager.get_user_mailbox_usage(user['id'])
            if usage['total_size_mb'] > 100:
                deleted_count = db_manager.cleanup_user_mailbox(user['id'], 100)
                if deleted_count > 0:
                    cleaned_users.append({
                        'username': user['username'],
                        'deleted_count': deleted_count,
                        'old_size': usage['total_size_mb']
                    })

        db_manager.disconnect()

        return jsonify({
            'success': True,
            'message': f'已清理 {len(cleaned_users)} 个用户的邮箱',
            'cleaned_users': cleaned_users
        })
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# 数据库初始化函数
def init_database_if_needed():
    """如果需要，初始化数据库"""
    try:
        print("🔍 检查数据库状态...")

        # 检查是否在Docker环境中
        is_docker = os.path.exists('/.dockerenv') or os.environ.get('FLASK_ENV') == 'production'

        if db_manager.connect():
            # 检查用户表是否存在且有数据
            try:
                result = db_manager.execute_query("SELECT COUNT(*) as count FROM users WHERE is_admin = 1")
                admin_count = result[0]['count'] if result else 0

                if admin_count == 0:
                    print("🔧 检测到空数据库，正在初始化...")

                    # 读取并执行init.sql
                    init_sql_path = os.path.join('database', 'init.sql')
                    if os.path.exists(init_sql_path):
                        with open(init_sql_path, 'r', encoding='utf-8') as f:
                            sql_content = f.read()

                        # 分割SQL语句并执行
                        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

                        for statement in sql_statements:
                            if statement.upper().startswith(('CREATE', 'INSERT', 'ALTER')):
                                try:
                                    db_manager.cursor.execute(statement)
                                    db_manager.connection.commit()
                                except Exception as e:
                                    if "already exists" not in str(e).lower():
                                        print(f"⚠️ SQL执行警告: {e}")

                        print("✅ 数据库初始化完成")
                    else:
                        print("⚠️ 找不到init.sql文件")
                else:
                    print(f"✅ 数据库已初始化，发现 {admin_count} 个管理员账号")

            except Exception as e:
                print(f"⚠️ 数据库检查异常: {e}")

            db_manager.disconnect()
            return True
        else:
            print("❌ 数据库连接失败")
            return False

    except Exception as e:
        print(f"❌ 数据库初始化异常: {e}")
        return False

# 启动应用
if __name__ == '__main__':
    try:
        print("🚀 启动Flask Web应用...")
        print("📍 访问地址: http://localhost:5000")
        print("🔐 管理员账号: admin/518107qW, longgekutta/518107qW")
        print("=" * 50)

        # 确保必要的目录存在
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('temp_attachments', exist_ok=True)
        os.makedirs('received_emails', exist_ok=True)

        # 初始化数据库
        if not init_database_if_needed():
            print("❌ 数据库初始化失败，请检查配置")
            if not os.path.exists('/.dockerenv'):  # 非Docker环境才等待用户输入
                input("按回车键退出...")
            sys.exit(1)

        # 生产环境配置
        app.run(
            host='127.0.0.1',  # 本地访问，更安全
            port=5000,
            debug=False,     # 生产环境关闭debug模式
            threaded=True,   # 启用多线程
            use_reloader=False  # 关闭自动重载
        )
    except Exception as e:
        print(f"❌ Flask应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
    except KeyboardInterrupt:
        print("\n📡 用户中断，正在关闭应用...")
    finally:
        print("👋 Flask应用已关闭")