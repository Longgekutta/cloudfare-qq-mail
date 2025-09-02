# -*- coding: utf-8 -*-
"""
运行时错误修复和环境验证脚本
检查并修复常见的部署和运行时问题
"""

import os
import sys
import time
import json
import mysql.connector
from mysql.connector import Error
import requests
import subprocess
import socket

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(level, message):
    """统一日志输出"""
    timestamp = time.strftime("%H:%M:%S")
    colors = {
        'INFO': Colors.CYAN,
        'SUCCESS': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'STEP': Colors.PURPLE
    }
    
    color = colors.get(level, Colors.WHITE)
    print(f"{color}[{timestamp}][{level}]{Colors.ENDC} {message}")

def check_environment_variables():
    """检查必要的环境变量"""
    log('STEP', '检查环境变量配置...')
    
    required_vars = {
        'DB_HOST': 'db',
        'DB_USER': 'root', 
        'DB_PASSWORD': '518107qW',
        'DB_NAME': 'cloudfare_qq_mail',
        'SECRET_KEY': 'cloudfare_qq_mail_secret_key_2025',
        'QQ_EMAIL': '2846117874@qq.com',
        'QQ_AUTH_CODE': 'ajqnryrvvjmsdcgi',
        'TARGET_DOMAIN': 'shiep.edu.kg'
    }
    
    missing_vars = []
    for var, default_value in required_vars.items():
        if not os.environ.get(var):
            os.environ[var] = default_value
            log('WARNING', f'环境变量 {var} 未设置，使用默认值: {default_value}')
            missing_vars.append(var)
        else:
            log('SUCCESS', f'环境变量 {var} = {os.environ.get(var)}')
    
    # 创建.env文件备份当前环境变量
    with open('.env.runtime', 'w', encoding='utf-8') as f:
        for var, default_value in required_vars.items():
            f.write(f'{var}={os.environ.get(var, default_value)}\n')
    
    log('SUCCESS', '环境变量检查完成')
    return len(missing_vars) == 0

def check_file_system():
    """检查文件系统和关键文件"""
    log('STEP', '检查文件系统...')
    
    # 检查关键文件
    critical_files = [
        'app.py',
        'config.py', 
        'database/init.sql',
        'database/db_manager.py',
        'requirements.txt',
        'docker-compose.yml'
    ]
    
    missing_files = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            log('SUCCESS', f'关键文件存在: {file_path}')
        else:
            log('ERROR', f'关键文件缺失: {file_path}')
            missing_files.append(file_path)
    
    # 检查并创建必要目录
    required_dirs = [
        'uploads',
        'temp_attachments', 
        'received_emails',
        'sent_attachments',
        'logs',
        'database/backup'
    ]
    
    for dir_path in required_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            # 设置目录权限
            os.chmod(dir_path, 0o755)
            log('SUCCESS', f'目录已准备: {dir_path}')
        except Exception as e:
            log('ERROR', f'无法创建目录 {dir_path}: {e}')
    
    log('SUCCESS', '文件系统检查完成')
    return len(missing_files) == 0

def check_database_connection():
    """检查数据库连接"""
    log('STEP', '检查数据库连接...')
    
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', '518107qW'),
        'database': os.environ.get('DB_NAME', 'cloudfare_qq_mail')
    }
    
    # 等待数据库服务
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            # 先测试主机连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((db_config['host'], 3306))
            sock.close()
            
            if result == 0:
                log('SUCCESS', f'数据库主机 {db_config["host"]}:3306 可达')
                break
            else:
                log('WARNING', f'等待数据库服务... ({attempt+1}/{max_attempts})')
                time.sleep(2)
                
        except Exception as e:
            log('WARNING', f'数据库连接测试失败: {e}')
            time.sleep(2)
    
    # 尝试连接数据库
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            log('SUCCESS', '数据库连接成功')
            
            # 检查数据库表
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                log('SUCCESS', f'数据库包含 {len(tables)} 个表')
                
                # 检查管理员账号
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
                admin_count = cursor.fetchone()[0]
                log('SUCCESS', f'发现 {admin_count} 个管理员账号')
                
            else:
                log('WARNING', '数据库为空，需要初始化')
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        log('ERROR', f'数据库连接失败: {e}')
        return False

def check_python_dependencies():
    """检查Python依赖"""
    log('STEP', '检查Python依赖...')
    
    required_packages = [
        'flask',
        'mysql-connector-python',
        'requests',
        'bcrypt',
        'werkzeug'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            log('SUCCESS', f'依赖包已安装: {package}')
        except ImportError:
            log('ERROR', f'缺少依赖包: {package}')
            missing_packages.append(package)
    
    if missing_packages:
        log('WARNING', '尝试安装缺失的依赖包...')
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            log('SUCCESS', '依赖包安装完成')
        except subprocess.CalledProcessError as e:
            log('ERROR', f'依赖包安装失败: {e}')
            return False
    
    log('SUCCESS', 'Python依赖检查完成')
    return True

def check_web_service():
    """检查Web服务"""
    log('STEP', '检查Web服务状态...')
    
    port = int(os.environ.get('WEB_PORT', 5000))
    
    # 检查端口占用
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        log('SUCCESS', f'Web服务在端口 {port} 运行')
        
        # 尝试HTTP请求
        try:
            response = requests.get(f'http://localhost:{port}', timeout=5)
            if response.status_code == 200:
                log('SUCCESS', 'Web服务响应正常')
                return True
            else:
                log('WARNING', f'Web服务响应异常: {response.status_code}')
                return False
        except requests.RequestException as e:
            log('ERROR', f'Web服务请求失败: {e}')
            return False
    else:
        log('WARNING', f'Web服务端口 {port} 未监听')
        return False

def fix_common_issues():
    """修复常见问题"""
    log('STEP', '修复常见问题...')
    
    fixes_applied = []
    
    # 修复1: 确保日志目录存在
    try:
        os.makedirs('logs', exist_ok=True)
        with open('logs/app.log', 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 系统检查完成\n")
        fixes_applied.append('日志目录修复')
    except Exception as e:
        log('ERROR', f'日志目录修复失败: {e}')
    
    # 修复2: 确保上传目录权限正确
    upload_dirs = ['uploads', 'temp_attachments', 'received_emails']
    for dir_name in upload_dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            os.chmod(dir_name, 0o755)
            fixes_applied.append(f'{dir_name}目录权限修复')
        except Exception as e:
            log('ERROR', f'{dir_name}目录权限修复失败: {e}')
    
    # 修复3: 创建数据库初始化标记文件
    try:
        with open('.db_initialized', 'w') as f:
            f.write(str(int(time.time())))
        fixes_applied.append('数据库初始化标记')
    except Exception as e:
        log('ERROR', f'数据库标记创建失败: {e}')
    
    if fixes_applied:
        log('SUCCESS', f'应用了 {len(fixes_applied)} 个修复: {", ".join(fixes_applied)}')
    else:
        log('INFO', '未发现需要修复的问题')

def generate_diagnostic_report():
    """生成诊断报告"""
    log('STEP', '生成诊断报告...')
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'environment': {
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'environment_variables': dict(os.environ)
        },
        'system_checks': {
            'file_system': check_file_system(),
            'database_connection': check_database_connection(), 
            'python_dependencies': check_python_dependencies(),
            'web_service': check_web_service()
        }
    }
    
    # 保存报告
    try:
        with open('diagnostic_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        log('SUCCESS', '诊断报告已保存: diagnostic_report.json')
    except Exception as e:
        log('ERROR', f'诊断报告保存失败: {e}')
    
    return report

def main():
    """主函数"""
    print(f"{Colors.CYAN}{'='*70}")
    print(f"🔧 运行时错误修复和环境验证工具")  
    print(f"{'='*70}{Colors.ENDC}")
    print(f"📅 检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}\n")
    
    success_count = 0
    total_checks = 5
    
    # 执行检查
    checks = [
        ('环境变量', check_environment_variables),
        ('文件系统', check_file_system),
        ('数据库连接', check_database_connection),
        ('Python依赖', check_python_dependencies),
        ('Web服务', check_web_service)
    ]
    
    for check_name, check_func in checks:
        try:
            if check_func():
                success_count += 1
        except Exception as e:
            log('ERROR', f'{check_name}检查失败: {e}')
    
    # 修复问题
    fix_common_issues()
    
    # 生成报告  
    generate_diagnostic_report()
    
    # 显示结果
    print(f"\n{Colors.CYAN}{'='*70}")
    print(f"📊 检查结果")
    print(f"{'='*70}{Colors.ENDC}")
    
    success_rate = (success_count / total_checks) * 100
    
    if success_rate == 100:
        log('SUCCESS', f'所有检查通过！({success_count}/{total_checks})')
        print(f"{Colors.GREEN}🎉 系统状态良好，可以正常运行！{Colors.ENDC}")
    elif success_rate >= 80:
        log('WARNING', f'大部分检查通过 ({success_count}/{total_checks})')
        print(f"{Colors.YELLOW}⚠️ 系统基本正常，但存在一些问题需要关注{Colors.ENDC}")
    else:
        log('ERROR', f'多项检查失败 ({success_count}/{total_checks})')
        print(f"{Colors.RED}❌ 系统存在严重问题，可能无法正常运行{Colors.ENDC}")
    
    print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}\n")
    
    # 提供解决建议
    if success_rate < 100:
        print(f"{Colors.YELLOW}🔧 问题解决建议：{Colors.ENDC}")
        print("1. 查看详细日志: diagnostic_report.json")
        print("2. 检查Docker服务状态: docker-compose ps")
        print("3. 查看容器日志: docker-compose logs -f")
        print("4. 重新部署: ./super-deploy.sh")
        print("5. 如仍有问题，请联系技术支持")
        
    return success_rate == 100

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log('INFO', '用户中断检查')
        sys.exit(1)
    except Exception as e:
        log('ERROR', f'检查过程出现异常: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
