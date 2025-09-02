#!/bin/bash
# Docker容器初始化脚本 - 增强版

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错

# 颜色输出定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必需的环境变量
check_env_vars() {
    log_info "检查环境变量..."
    
    local required_vars=("DB_HOST" "DB_USER" "DB_PASSWORD" "DB_NAME")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "缺少必需的环境变量: ${missing_vars[*]}"
        exit 1
    fi
    
    log_success "环境变量检查完成"
}

# 等待MySQL服务启动的增强版本
wait_for_mysql() {
    log_info "等待MySQL服务启动..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
            log_success "MySQL服务已启动 (尝试 $attempt/$max_attempts)"
            return 0
        fi
        
        log_info "等待MySQL启动... (尝试 $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "MySQL服务启动超时，请检查数据库配置"
    exit 1
}

# 创建数据库
create_database() {
    log_info "创建数据库..."
    
    if mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null; then
        log_success "数据库 $DB_NAME 创建成功"
    else
        log_error "数据库创建失败"
        exit 1
    fi
}

# 执行数据库初始化
init_database() {
    log_info "执行数据库初始化..."
    
    local init_file="/app/database/init.sql"
    
    if [ ! -f "$init_file" ]; then
        log_error "未找到数据库初始化文件: $init_file"
        exit 1
    fi
    
    if mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$init_file" 2>/dev/null; then
        log_success "数据库初始化完成"
    else
        log_error "数据库初始化失败"
        exit 1
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    local dirs=("/app/uploads" "/app/temp_attachments" "/app/received_emails" "/app/sent_attachments")
    
    for dir in "${dirs[@]}"; do
        if mkdir -p "$dir" && chmod 755 "$dir"; then
            log_info "创建目录: $dir"
        else
            log_error "无法创建目录: $dir"
            exit 1
        fi
    done
    
    log_success "目录创建完成"
}

# 验证管理员账号
verify_admin_account() {
    log_info "验证管理员账号..."
    
    local admin_count
    admin_count=$(mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -sN -e "SELECT COUNT(*) FROM users WHERE is_admin = 1;" 2>/dev/null)
    
    if [ "$admin_count" -gt 0 ]; then
        log_success "发现 $admin_count 个管理员账号"
    else
        log_warning "未发现管理员账号，请检查数据库初始化"
    fi
}

# 健康检查
health_check() {
    log_info "执行系统健康检查..."
    
    # 检查关键文件
    local critical_files=("/app/app.py" "/app/requirements.txt" "/app/database/init.sql")
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "关键文件缺失: $file"
            exit 1
        fi
    done
    
    # 检查Python依赖
    if ! python -c "import flask, pymysql" 2>/dev/null; then
        log_error "Python依赖缺失，请检查requirements.txt安装"
        exit 1
    fi
    
    log_success "系统健康检查通过"
}

echo "🚀 Docker容器初始化开始..."
echo "======================================"

# 执行初始化步骤
check_env_vars
wait_for_mysql
create_database
init_database
create_directories
verify_admin_account
health_check

echo "======================================"
log_success "Docker容器初始化完成"
echo "🌐 启动Flask应用..."

# 运行环境验证和错误修复
echo "🔧 运行环境验证..."
python fix-runtime-errors.py || {
    log_warning "环境验证发现问题，但继续启动应用"
}

# 启动Flask应用
log_info "启动Flask应用..."
exec python app.py
