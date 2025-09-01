# -*- coding: utf-8 -*-
"""
Flask Web应用主文件（带用户隔离功能）
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库管理模块
from database.db_manager import DatabaseManager

# 创建Flask应用
app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = 'cloudfare_qq_mail_secret_key_2025'  # 在生产环境中应该使用更安全的密钥

# 创建数据库管理器实例
db_manager = DatabaseManager()

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
            # 使用bcrypt验证密码
            import bcrypt
            try:
                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    # 登录成功，设置会话
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    return redirect(url_for('index'))
                else:
                    # 密码错误
                    return render_template('login.html', error='用户名或密码错误')
            except Exception as e:
                # 密码验证出错，可能是密码格式问题
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
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 检查密码是否匹配
        if password != confirm_password:
            return render_template('register.html', error='密码不匹配')
        
        # 检查用户名是否已存在
        user = None
        if db_manager.connect():
            user = db_manager.get_user_by_username(username)
            db_manager.disconnect()
        
        if user:
            return render_template('register.html', error='用户名已存在')
        
        # 创建新用户
        if db_manager.connect():
            # 对密码进行bcrypt加密
            import bcrypt
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            result = db_manager.create_user(username, hashed_password)
            db_manager.disconnect()
            
            if result > 0:
                # 注册成功，重定向到登录页面
                return redirect(url_for('login'))
            else:
                # 注册失败，返回错误信息
                return render_template('register.html', error='注册失败')
        else:
            return render_template('register.html', error='数据库连接失败')
    
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
    邮件列表页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取邮件列表（基于用户邮箱实现隔离）
    mail_list = []
    if db_manager.connect():
        mail_list = db_manager.get_user_emails_with_isolation(user_id=session['user_id'])
        db_manager.disconnect()
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染邮件列表页面模板
    return render_template('mails.html', mails=mail_list, user=user)

# 收件箱页面路由
@app.route('/inbox')
def inbox():
    """
    收件箱页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取收件邮件列表（基于用户邮箱实现隔离）
    mail_list = []
    user_emails = []
    if db_manager.connect():
        mail_list = db_manager.get_user_inbox_emails(user_id=session['user_id'])
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染收件箱页面模板
    return render_template('inbox.html', mails=mail_list, user=user, user_emails=user_emails)

# 发件箱页面路由
@app.route('/outbox')
def outbox():
    """
    发件箱页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取发件邮件列表（基于用户邮箱实现隔离）
    mail_list = []
    user_emails = []
    if db_manager.connect():
        mail_list = db_manager.get_user_outbox_emails(user_id=session['user_id'])
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染发件箱页面模板
    return render_template('outbox.html', mails=mail_list, user=user, user_emails=user_emails)

# 写邮件页面路由
@app.route('/compose', methods=['GET', 'POST'])
def compose():
    """
    写邮件页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取用户邮箱列表
    user_emails = []
    if db_manager.connect():
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    if request.method == 'POST':
        # 处理写邮件表单提交
        from_email = request.form['from_email']
        to_email = request.form['to_email']
        subject = request.form['subject']
        content = request.form['content']
        
        # 保存邮件
        if db_manager.connect():
            # 这里应该实现邮件发送和保存逻辑
            # 为简化起见，我们只保存到数据库
            from datetime import datetime
            result = db_manager.save_email(from_email, to_email, subject, content, datetime.now())
            db_manager.disconnect()
            
            if result > 0:
                return redirect(url_for('outbox'))
            else:
                return render_template('compose.html', user_emails=user_emails, user=user, error='邮件发送失败')
        else:
            return render_template('compose.html', user_emails=user_emails, user=user, error='数据库连接失败')
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # GET请求，渲染写邮件页面模板
    return render_template('compose.html', user=user, user_emails=user_emails)

# 注册邮箱页面路由
@app.route('/register_email', methods=['GET', 'POST'])
def register_email():
    """
    注册邮箱页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取用户邮箱列表
    user_emails = []
    domains = []
    if db_manager.connect():
        user_emails = db_manager.get_user_emails(session['user_id'])
        domains = db_manager.get_all_domains()
        db_manager.disconnect()
    
    if request.method == 'POST':
        # 处理注册邮箱表单提交
        email_address = request.form['email_address']
        domain_id = request.form['domain_id']
        
        # 创建用户邮箱
        if db_manager.connect():
            result = db_manager.create_user_email(session['user_id'], email_address, domain_id)
            db_manager.disconnect()
            
            if result > 0:
                return redirect(url_for('register_email'))
            else:
                return render_template('register_email.html', user_emails=user_emails, domains=domains, user=user, error='邮箱注册失败')
        else:
            return render_template('register_email.html', user_emails=user_emails, domains=domains, user=user, error='数据库连接失败')
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染注册邮箱页面模板
    return render_template('register_email.html', user=user, user_emails=user_emails, domains=domains)

# 邮件详情页面路由
@app.route('/mail/<int:mail_id>')
def mail_detail(mail_id):
    """
    邮件详情页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取邮件详情（基于用户邮箱实现隔离）
    mail = {}
    if db_manager.connect():
        mail = db_manager.get_user_email_by_id_with_isolation(email_id=mail_id, user_id=session['user_id'])
        db_manager.disconnect()
    
    # 获取当前用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染邮件详情页面模板
    return render_template('mail_detail.html', mail=mail, user=user)

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
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return redirect(url_for('index'))
    
    # 获取用户列表
    user_list = []
    if db_manager.connect():
        user_list = db_manager.get_all_users()
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
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return redirect(url_for('index'))
    
    # 获取域名列表
    domain_list = []
    if db_manager.connect():
        domain_list = db_manager.get_all_domains()
        db_manager.disconnect()
    
    # 渲染域名管理页面模板
    return render_template('admin_domains.html', domains=domain_list, user=user)

# 用户信息页面路由
@app.route('/profile')
def profile():
    """
    用户信息页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取用户信息
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    # 渲染用户信息页面模板
    return render_template('profile.html', user=user)

# API端点：获取邮件列表
@app.route('/api/mails')
def api_mails():
    """
    获取邮件列表的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 获取邮件列表（基于用户邮箱实现隔离）
    mail_list = []
    if db_manager.connect():
        mail_list = db_manager.get_user_emails_with_isolation(user_id=session['user_id'])
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
    
    # 获取邮件详情（基于用户邮箱实现隔离）
    mail = {}
    if db_manager.connect():
        mail = db_manager.get_user_email_by_id_with_isolation(email_id=mail_id, user_id=session['user_id'])
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
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return jsonify({'error': '权限不足'}), 403
    
    # 获取用户列表
    user_list = []
    if db_manager.connect():
        user_list = db_manager.get_all_users()
        db_manager.disconnect()
    
    return jsonify(user_list)

# API端点：添加用户
@app.route('/api/admin/users', methods=['POST'])
def api_add_user():
    """
    添加用户的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return jsonify({'error': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_vip = data.get('is_vip', False)
    balance = data.get('balance', 0.0)
    
    # 创建用户
    if db_manager.connect():
        # 对密码进行bcrypt加密
        import bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        result = db_manager.create_user(username, hashed_password, is_vip, balance)
        db_manager.disconnect()
        
        if result > 0:
            return jsonify({'success': True, 'message': '用户创建成功'})
        else:
            return jsonify({'success': False, 'message': '用户创建失败'}), 500
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# API端点：更新用户
@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    """
    更新用户的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return jsonify({'error': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    is_vip = data.get('is_vip', False)
    balance = data.get('balance', 0.0)
    
    # 更新用户
    if db_manager.connect():
        result = db_manager.update_user(user_id, username, email, is_vip, balance)
        db_manager.disconnect()
        
        if result > 0:
            return jsonify({'success': True, 'message': '用户更新成功'})
        else:
            return jsonify({'success': False, 'message': '用户更新失败'}), 500
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
        return jsonify({'error': '未登录'}), 401
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return jsonify({'error': '权限不足'}), 403
    
    # 删除用户
    if db_manager.connect():
        result = db_manager.delete_user(user_id)
        db_manager.disconnect()
        
        if result > 0:
            return jsonify({'success': True, 'message': '用户删除成功'})
        else:
            return jsonify({'success': False, 'message': '用户删除失败'}), 500
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# API端点：获取所有域名（仅管理员可见）
@app.route('/api/admin/domains')
def api_admin_domains():
    """
    获取所有域名的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return jsonify({'error': '权限不足'}), 403
    
    # 获取域名列表
    domain_list = []
    if db_manager.connect():
        domain_list = db_manager.get_all_domains()
        db_manager.disconnect()
    
    return jsonify(domain_list)

# API端点：添加域名
@app.route('/api/admin/domains', methods=['POST'])
def api_add_domain():
    """
    添加域名的API端点
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 检查用户是否为管理员
    user = None
    if db_manager.connect():
        user = db_manager.get_user_by_username(session['username'])
        db_manager.disconnect()
    
    if not user or not user['is_vip']:
        return jsonify({'error': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json()
    domain_name = data.get('domain_name')
    
    # 创建域名
    if db_manager.connect():
        result = db_manager.create_domain(domain_name)
        db_manager.disconnect()
        
        if result > 0:
            return jsonify({'success': True, 'message': '域名创建成功'})
        else:
            return jsonify({'success': False, 'message': '域名创建失败'}), 500
    else:
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500

# 启动应用
if __name__ == '__main__':
    app.run(debug=True)