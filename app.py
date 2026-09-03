# -*- coding: utf-8 -*-
"""
Flask Web应用主文件（入口）
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
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    import secrets
    _secret_key = secrets.token_hex(32)
    print('⚠️ 未设置 SECRET_KEY，已生成临时会话密钥；重启后会话将失效，请在 .env 中配置固定密钥')
app.secret_key = _secret_key

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
            # 使用bcrypt验证密码，兼容明文密码（迁移期）
            import bcrypt
            stored_password = user['password']
            
            # 密码格式检测：bcrypt哈希以$2开头
            if stored_password.startswith('$2'):
                try:
                    password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                except Exception:
                    password_valid = False
            else:
                # 兼容旧版本明文密码（需改进为仅用于迁移）
                password_valid = (password == stored_password)
                if password_valid:
                    # 自动升级为bcrypt哈希
                    try:
                        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        if db_manager.connect():
                            db_manager.execute_query(
                                "UPDATE users SET password = %s WHERE id = %s",
                                (hashed, user['id'])
                            )
                            db_manager.disconnect()
                    except Exception:
                        pass  # 升级失败不影响登录
            
            if password_valid:
                # 登录成功，设置会话（重新生成ID防会话固定）
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='用户名或密码错误')
        else:
            # 用户不存在（为防用户枚举，返回相同错误信息）
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
        
        # 对密码进行bcrypt哈希处理
        import bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 保存用户到数据库
        success = False
        if db_manager.connect():
            success = db_manager.execute_query(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            db_manager.disconnect()
        
        if success:
            # 注册成功，跳转到登录页面
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error='注册失败，请重试')
    
    # GET请求，渲染注册页面
    return render_template('register.html')

# 登出路由
@app.route('/logout')
def logout():
    """
    登出视图函数
    """
    session.clear()
    return redirect(url_for('index'))

# 邮箱列表页面路由
@app.route('/mails')
def mails():
    """
    邮箱列表页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取用户邮箱列表
    user_emails = []
    if db_manager.connect():
        user_emails = db_manager.get_user_emails(session['user_id'])
        db_manager.disconnect()
    
    return render_template('mails.html', emails=user_emails)

# 写邮件页面路由
@app.route('/compose')
def compose():
    """
    写邮件页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('compose.html')

# 收件箱页面路由
@app.route('/inbox')
def inbox():
    """
    收件箱页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('inbox.html')

# 发件箱页面路由
@app.route('/outbox')
def outbox():
    """
    发件箱页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('outbox.html')

# 用户资料页面路由
@app.route('/profile')
def profile():
    """
    用户资料页面视图函数
    """
    # 检查用户是否已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('profile.html')