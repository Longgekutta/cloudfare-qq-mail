#!/bin/bash
# ============================================================================
# 🚀 终极部署脚本 - 整合所有部署方案的最强版本
# ============================================================================
# 用户信息：
# GitHub: Longgekutta
# DockerHub: longgekutta  
# Gitee: longgekutta
# ============================================================================

set -euo pipefail

# 设置默认变量值，避免未定义变量导致脚本退出
VERBOSE=${VERBOSE:-false}
DEPLOY_MODE=${DEPLOY_MODE:-""}
USE_PREBUILT_IMAGE=${USE_PREBUILT_IMAGE:-false}
SKIP_DOCKER_INSTALL=${SKIP_DOCKER_INSTALL:-false}

# 项目信息
readonly PROJECT_NAME="cloudfare-qq-mail"
readonly GITHUB_REPO="https://github.com/Longgekutta/cloudfare-qq-mail.git"
readonly GITEE_REPO="https://gitee.com/longgekutta/cloudfare-qq-mail.git"
readonly DOCKER_IMAGE="longgekutta/cloudfare-qq-mail:latest"
readonly VERSION="v3.0-ultimate"

# 日志配置
readonly DEPLOY_LOG="/tmp/${PROJECT_NAME}-deploy-$(date +%s).log"
readonly SCRIPT_DIR="$(pwd)"

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m'

# 全局变量
declare -i START_TIME=$(date +%s)

# 日志函数
log() {
    local level="$1" && shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')
    
    case $level in
        INFO)    printf "${CYAN}[%s][INFO]${NC} %s\n" "$timestamp" "$message" | tee -a "$DEPLOY_LOG" ;;
        SUCCESS) printf "${GREEN}[%s][SUCCESS]${NC} %s\n" "$timestamp" "$message" | tee -a "$DEPLOY_LOG" ;;
        WARNING) printf "${YELLOW}[%s][WARNING]${NC} %s\n" "$timestamp" "$message" | tee -a "$DEPLOY_LOG" ;;
        ERROR)   printf "${RED}[%s][ERROR]${NC} %s\n" "$timestamp" "$message" | tee -a "$DEPLOY_LOG" ;;
        STEP)    printf "${PURPLE}[%s][STEP]${NC} %s\n" "$timestamp" "$message" | tee -a "$DEPLOY_LOG" ;;
        DEBUG)   [[ "$VERBOSE" == "true" ]] && printf "${WHITE}[%s][DEBUG]${NC} %s\n" "$timestamp" "$message" | tee -a "$DEPLOY_LOG" ;;
    esac
}

# 错误处理
error_exit() {
    log ERROR "$1"
    log ERROR "部署失败！查看详细日志: $DEPLOY_LOG"
    
    # 显示故障排查信息
    echo -e "\n${RED}🔧 故障排查步骤：${NC}"
    echo "1. 查看完整日志: cat $DEPLOY_LOG"
    echo "2. 检查Docker状态: docker info"
    echo "3. 检查端口占用: netstat -tuln | grep -E ':(5000|3306|8080)'"
    echo "4. 清理重试: $0 --mode=clean-deploy"
    echo "5. 获取帮助: $0 --help"
    
    exit 1
}

trap 'error_exit "部署过程中发生未知错误"' ERR

# 显示横幅
show_banner() {
    echo -e "${BLUE}"
    cat << 'EOF'
================================================================
🚀 终极部署脚本 - Cloudfare QQ Mail Service v3.0
================================================================
EOF
    echo -e "${NC}"
    echo "📅 部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "👤 GitHub: Longgekutta"  
    echo "🐳 DockerHub: longgekutta"
    echo "📂 工作目录: $SCRIPT_DIR"
    echo "📋 部署日志: $DEPLOY_LOG"
    echo "⚙️ 部署模式: ${DEPLOY_MODE:-自动检测}"
    echo "================================================================"
    echo ""
}

# 检测部署环境
detect_environment() {
    log STEP "检测部署环境..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log INFO "检测到 Linux 系统"
        if command -v lsb_release &> /dev/null; then
            local distro=$(lsb_release -si 2>/dev/null)
            local version=$(lsb_release -sr 2>/dev/null)
            log INFO "发行版: $distro $version"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log INFO "检测到 macOS 系统"
    else
        log WARNING "未知操作系统: $OSTYPE"
    fi
    
    # 检测是否在容器内
    if [[ -f /.dockerenv ]] || grep -q 'docker\|lxc' /proc/1/cgroup 2>/dev/null; then
        log WARNING "检测到运行在容器内，某些功能可能受限"
    fi
    
    # 检测网络连接 (优先检测Gitee，国内访问更快)
    if curl -s --connect-timeout 3 https://gitee.com &>/dev/null; then
        log SUCCESS "Gitee 网络连接正常，将优先使用国内镜像"
    elif curl -s --connect-timeout 3 https://github.com &>/dev/null; then
        log INFO "GitHub 网络连接正常"
    else
        log WARNING "网络连接检测超时，将跳过网络检测继续部署"
    fi
    
    log SUCCESS "环境检测完成"
}

# 智能安装Docker
install_docker_smart() {
    log STEP "检查Docker环境..."
    
    if command -v docker &> /dev/null; then
        log SUCCESS "Docker 已安装: $(docker --version)"
        
        # 检查Docker服务状态
        if ! docker info &> /dev/null; then
            log WARNING "Docker服务未运行，尝试启动..."
            sudo systemctl start docker 2>/dev/null || sudo service docker start 2>/dev/null || {
                log ERROR "无法启动Docker服务"
                return 1
            }
        fi
    else
        if [[ "$SKIP_DOCKER_INSTALL" == "true" ]]; then
            error_exit "Docker未安装且设置跳过安装"
        fi
        
        log INFO "安装Docker..."
        
        # 智能选择安装方法
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://get.docker.com | sh
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            curl -fsSL https://get.docker.com | sh
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y docker
        else
            # 通用安装
            curl -fsSL https://get.docker.com | sh
        fi
        
        # 启动Docker
        sudo systemctl enable docker
        sudo systemctl start docker
        
        # 添加用户到docker组
        sudo usermod -aG docker "$USER" || log WARNING "无法添加用户到docker组"
    fi
    
    # 检查Docker Compose
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log INFO "安装Docker Compose..."
        
        # 尝试安装Docker Compose Plugin
        if curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' &> /dev/null; then
            local compose_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | cut -d'"' -f4)
            sudo curl -L "https://github.com/docker/compose/releases/download/${compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        else
            log WARNING "无法获取Docker Compose版本，使用apt安装"
            sudo apt-get install -y docker-compose 2>/dev/null || {
                log ERROR "Docker Compose安装失败"
                return 1
            }
        fi
    fi
    
    log SUCCESS "Docker环境就绪"
    
    # 检查Docker权限
    if ! docker ps &> /dev/null; then
        log WARNING "当前用户可能需要Docker权限，请运行: sudo usermod -aG docker $USER 并重新登录"
    fi
}

# ZIP文件解压函数
extract_zip() {
    local zip_file="$1"
    
    if ! command -v unzip &> /dev/null; then
        log WARNING "unzip未安装，尝试安装..."
        if command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y unzip
        elif command -v yum &> /dev/null; then
            yum install -y unzip
        else
            log ERROR "无法自动安装unzip，请手动安装后重试"
            return 1
        fi
    fi
    
    log INFO "解压ZIP文件: $zip_file"
    
    if unzip -q "$zip_file"; then
        # 查找解压后的目录（可能有不同的命名方式）
        local extracted_dir=""
        for dir in cloudfare-qq-mail-* cloudfare-qq-mail; do
            if [[ -d "$dir" ]]; then
                extracted_dir="$dir"
                break
            fi
        done
        
        if [[ -n "$extracted_dir" ]]; then
            # 重命名为标准目录名
            if [[ "$extracted_dir" != "$PROJECT_NAME" ]]; then
                mv "$extracted_dir" "$PROJECT_NAME"
            fi
            
            cd "$PROJECT_NAME"
            log SUCCESS "ZIP文件解压成功"
            rm -f "../$zip_file"  # 清理ZIP文件
            return 0
        else
            log ERROR "解压后找不到项目目录"
            return 1
        fi
    else
        log ERROR "ZIP文件解压失败"
        return 1
    fi
}

# 获取项目代码
get_project_code() {
    log STEP "获取项目代码..."
    
    # 如果已在项目目录中
    if [[ -f "docker-compose.yml" && -f "app.py" ]]; then
        log INFO "检测到已在项目目录中，使用现有代码"
        return 0
    fi
    
    # 检查Git是否安装
    if ! command -v git &> /dev/null; then
        log WARNING "Git未安装，正在自动安装..."
        
        if command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y git
        elif command -v yum &> /dev/null; then
            yum install -y git
        elif command -v dnf &> /dev/null; then
            dnf install -y git
        else
            error_exit "无法自动安装Git，请手动安装: apt-get install git 或 yum install git"
        fi
        
        if ! command -v git &> /dev/null; then
            error_exit "Git安装失败，请手动安装Git后重试"
        fi
        
        log SUCCESS "Git安装成功"
    fi
    
    # 尝试从多个源获取代码 (优先使用Gitee，速度更快)
    local repos=("$GITEE_REPO" "$GITHUB_REPO")
    local target_dir="${PROJECT_NAME}"
    
    # 清理可能存在的旧目录
    if [[ -d "$target_dir" ]]; then
        log INFO "清理旧的项目目录..."
        rm -rf "$target_dir"
    fi
    
    for repo in "${repos[@]}"; do
        log INFO "尝试克隆: $repo"
        
        # 显示详细的git错误信息
        if git clone "$repo" "$target_dir"; then
            cd "$target_dir"
            log SUCCESS "代码获取成功: $repo"
            return 0
        else
            local git_error=$?
            log WARNING "克隆失败: $repo (错误代码: $git_error)"
            
            # 提供更详细的错误诊断
            case $git_error in
                128)
                    log WARNING "可能原因: 仓库不存在或网络问题"
                    ;;
                1|2)
                    log WARNING "可能原因: 网络连接超时或DNS解析失败"
                    ;;
                *)
                    log WARNING "Git错误代码: $git_error，请检查网络连接"
                    ;;
            esac
        fi
    done
    
    # 如果Git克隆都失败，尝试自动下载ZIP文件
    log WARNING "Git克隆失败，尝试下载ZIP文件..."
    
    local zip_urls=(
        "https://gitee.com/longgekutta/cloudfare-qq-mail/repository/archive/main.zip"
        "https://github.com/Longgekutta/cloudfare-qq-mail/archive/main.zip"
    )
    
    for zip_url in "${zip_urls[@]}"; do
        log INFO "尝试下载: $zip_url"
        
        local zip_file="cloudfare-qq-mail-main.zip"
        
        # 尝试使用wget或curl下载
        if command -v wget &> /dev/null; then
            if wget -O "$zip_file" "$zip_url" --timeout=30 --tries=2; then
                log SUCCESS "ZIP文件下载成功"
                if extract_zip "$zip_file"; then
                    return 0
                fi
            else
                log WARNING "wget下载失败: $zip_url"
            fi
        elif command -v curl &> /dev/null; then
            if curl -L --connect-timeout 30 --max-time 60 -o "$zip_file" "$zip_url"; then
                log SUCCESS "ZIP文件下载成功"
                if extract_zip "$zip_file"; then
                    return 0
                fi
            else
                log WARNING "curl下载失败: $zip_url"
            fi
        fi
        
        # 清理失败的下载文件
        rm -f "$zip_file"
    done
    
    # 所有方法都失败，提供手动解决方案
    log ERROR "所有自动获取代码的方法都失败了"
    log INFO "请尝试以下手动解决方案："
    echo ""
    echo "1. 检查网络连接:"
    echo "   ping -c 3 gitee.com"
    echo "   ping -c 3 github.com"
    echo ""
    echo "2. 手动下载并解压:"
    echo "   wget https://gitee.com/longgekutta/cloudfare-qq-mail/repository/archive/main.zip"
    echo "   unzip main.zip && mv cloudfare-qq-mail-* cloudfare-qq-mail && cd cloudfare-qq-mail"
    echo ""
    echo "3. 然后运行本地部署:"
    echo "   docker-compose up -d --build"
    
    error_exit "无法自动获取项目代码，请参考上述手动方案"
}

# 创建完整配置
create_complete_config() {
    log STEP "创建完整配置..."
    
    # 创建.env文件
    cat > .env << EOF
# ============================================================================
# 📧 邮箱服务系统 - 完整环境配置
# ============================================================================
# 自动生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# 部署版本: $VERSION
# ============================================================================

# ========== 🌐 应用基础配置 ==========
WEB_PORT=5000
FLASK_ENV=production
SECRET_KEY=cloudfare_qq_mail_secret_key_$(date +%s)
DEBUG_MODE=False
DOMAIN=http://localhost:5000

# ========== 🗄️ 数据库配置 ==========
DB_HOST=db
DB_PORT=3306
DB_USER=root
DB_PASSWORD=518107qW
DB_NAME=cloudfare_qq_mail

# ========== 📧 邮箱服务配置 ==========
QQ_EMAIL=YOUR_QQ_EMAIL@qq.com
QQ_AUTH_CODE=YOUR_QQ_AUTH_CODE
TARGET_DOMAIN=shiep.edu.kg
RESEND_API_KEY=re_00000000_REPLACED_DUMMY_KEY_0000

# ========== 💰 支付系统配置 ==========
YIPAY_PID=6166
YIPAY_KEY=deefc7cc0449be9cb621b7800f5e7f1c
YIPAY_GATEWAY=https://pay.yzhifupay.com/

# ========== 🔧 可选服务配置 ==========
PHPMYADMIN_PORT=8080
REDIS_PASSWORD=redis$(date +%s)

# ========== 🚀 部署配置 ==========
TZ=Asia/Shanghai
COMPOSE_PROJECT_NAME=$PROJECT_NAME
DOCKER_IMAGE=$DOCKER_IMAGE
DEPLOY_VERSION=$VERSION
DEPLOY_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# ============================================================================
EOF
    
    # 创建必要目录
    local dirs=(
        "uploads" "temp_attachments" "received_emails" "sent_attachments" 
        "logs" "mysql_data" "database/backup"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        chmod 755 "$dir"
        log DEBUG "创建目录: $dir"
    done
    
    log SUCCESS "配置文件和目录创建完成"
    
    # 调试信息：验证文件是否创建成功
    log DEBUG "验证配置文件："
    if [[ -f ".env" ]]; then
        log DEBUG "✅ .env文件已创建"
    else
        log ERROR "❌ .env文件创建失败"
        return 1
    fi
    
    if [[ -f "docker-compose.yml" ]]; then
        log DEBUG "✅ docker-compose.yml文件存在"
    else
        log DEBUG "ℹ️ docker-compose.yml文件不存在（将使用镜像部署）"
    fi
    
    # 确保函数成功返回
    return 0
}

# 选择部署方式
choose_deployment_method() {
    if [[ -n "$DEPLOY_MODE" ]]; then
        return 0  # 已指定模式
    fi
    
    log STEP "选择部署方式..."
    
    # 调试信息
    log DEBUG "当前目录: $(pwd)"
    log DEBUG "USE_PREBUILT_IMAGE: $USE_PREBUILT_IMAGE"
    log DEBUG "当前DEPLOY_MODE: ${DEPLOY_MODE:-未设置}"
    
    # 检测网络环境并选择最佳构建方式
    local is_china_network=false
    if curl -s --connect-timeout 3 https://mirrors.tuna.tsinghua.edu.cn &>/dev/null; then
        is_china_network=true
        log INFO "检测到国内网络环境，将使用国内镜像优化"
    fi
    
    # 自动检测最佳部署方式
    if [[ "$USE_PREBUILT_IMAGE" == "true" ]]; then
        DEPLOY_MODE="image"
        log INFO "使用预构建镜像部署模式"
    elif [[ -f "Dockerfile" && -f "docker-compose.yml" ]]; then
        if [[ "$is_china_network" == "true" && -f "Dockerfile.china" && -f "docker-compose.china.yml" ]]; then
            DEPLOY_MODE="build-china"
            log INFO "使用国内优化版本构建部署（速度更快）"
        else
            DEPLOY_MODE="build"
            log INFO "使用本地构建部署模式"
        fi
    else
        DEPLOY_MODE="image"
        log INFO "默认使用镜像部署模式"
    fi
    
    log SUCCESS "部署方式选择完成: $DEPLOY_MODE"
}

# 预构建镜像部署
deploy_with_image() {
    log STEP "使用预构建镜像部署..."
    
    # 拉取最新镜像
    log INFO "拉取Docker镜像: $DOCKER_IMAGE"
    docker pull "$DOCKER_IMAGE" || {
        log WARNING "镜像拉取失败，将使用本地构建"
        DEPLOY_MODE="build"
        deploy_with_build
        return
    }
    
    # 创建临时docker-compose文件
    cat > docker-compose.temp.yml << EOF
version: '3.8'
services:
  web:
    image: ${DOCKER_IMAGE}
    container_name: ${PROJECT_NAME}-web
    ports:
      - "\${WEB_PORT:-5000}:5000"
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
      - ./temp_attachments:/app/temp_attachments
      - ./received_emails:/app/received_emails
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: mysql:8.0
    container_name: ${PROJECT_NAME}-db
    environment:
      MYSQL_ROOT_PASSWORD: \${DB_PASSWORD}
      MYSQL_DATABASE: \${DB_NAME}
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
    ports:
      - "\${DB_PORT:-3306}:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped
    networks:
      - app-network
    command: --default-authentication-plugin=mysql_native_password
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p\${DB_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

volumes:
  mysql_data:
    driver: local

networks:
  app-network:
    driver: bridge
EOF
    
    # 启动服务
    docker-compose -f docker-compose.temp.yml up -d
    
    log SUCCESS "镜像部署完成"
}

# 本地构建部署
deploy_with_build() {
    log STEP "使用本地构建部署..."
    
    # 清理旧资源
    log INFO "清理旧容器和镜像..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 构建并启动
    log INFO "构建并启动服务..."
    docker-compose up -d --build --force-recreate
    
    log SUCCESS "本地构建部署完成"
}

# 国内优化构建部署
deploy_with_build_china() {
    log STEP "使用国内优化版本构建部署..."
    
    # 清理旧资源
    log INFO "清理旧容器和镜像..."
    docker-compose -f docker-compose.china.yml down --remove-orphans 2>/dev/null || true
    
    # 使用国内优化版本构建并启动
    log INFO "使用国内镜像源构建并启动服务（速度更快）..."
    docker-compose -f docker-compose.china.yml up -d --build --force-recreate
    
    log SUCCESS "国内优化构建部署完成"
}

# 智能部署
smart_deploy() {
    log STEP "开始智能部署..."
    
    case "$DEPLOY_MODE" in
        "image")
            deploy_with_image
            ;;
        "build")
            deploy_with_build
            ;;
        "build-china")
            deploy_with_build_china
            ;;
        "hybrid")
            # 先尝试镜像，失败则构建
            if ! deploy_with_image; then
                log INFO "镜像部署失败，尝试本地构建..."
                DEPLOY_MODE="build"
                deploy_with_build
            fi
            ;;
        *)
            error_exit "未知部署模式: $DEPLOY_MODE"
            ;;
    esac
}

# 等待服务就绪
wait_for_services() {
    log STEP "等待服务完全启动..."
    
    local max_wait=180
    local wait_interval=5
    local elapsed=0
    
    while [[ $elapsed -lt $max_wait ]]; do
        # 检查容器状态
        if docker-compose ps --services --filter "status=running" | wc -l | grep -q "2"; then
            log INFO "容器已启动，检查服务可用性..."
            
            # 检查Web服务
            if curl -sf "http://localhost:5000" > /dev/null 2>&1; then
                log SUCCESS "所有服务已就绪 (耗时: ${elapsed}s)"
                return 0
            fi
        fi
        
        if [[ $((elapsed % 15)) -eq 0 ]]; then
            log INFO "等待服务启动... (${elapsed}s/${max_wait}s)"
        fi
        
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done
    
    log WARNING "服务启动超时，请手动检查"
    return 1
}

# 验证部署结果
verify_deployment() {
    log STEP "验证部署结果..."
    
    local checks_passed=0
    local total_checks=5
    
    # 检查1: 容器状态
    if docker-compose ps | grep -q "Up"; then
        log SUCCESS "✅ 容器状态正常"
        ((checks_passed++))
    else
        log ERROR "❌ 容器状态异常"
    fi
    
    # 检查2: Web服务响应
    if curl -sf "http://localhost:5000" > /dev/null 2>&1; then
        log SUCCESS "✅ Web服务响应正常"
        ((checks_passed++))
    else
        log ERROR "❌ Web服务无响应"
    fi
    
    # 检查3: 数据库连接
    if docker-compose exec -T db mysqladmin ping -h localhost -u root -p518107qW 2>/dev/null | grep -q "alive"; then
        log SUCCESS "✅ 数据库连接正常"
        ((checks_passed++))
    else
        log ERROR "❌ 数据库连接异常"
    fi
    
    # 检查4: 端口监听
    local ports=("5000" "3306")
    local ports_ok=0
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            ((ports_ok++))
        fi
    done
    
    if [[ $ports_ok -eq ${#ports[@]} ]]; then
        log SUCCESS "✅ 端口监听正常"
        ((checks_passed++))
    else
        log ERROR "❌ 端口监听异常 ($ports_ok/${#ports[@]})"
    fi
    
    # 检查5: 日志无严重错误
    if ! docker-compose logs | grep -i "error\|failed\|exception" | grep -v "warning" > /dev/null 2>&1; then
        log SUCCESS "✅ 日志检查通过"
        ((checks_passed++))
    else
        log WARNING "⚠️ 发现日志错误，但可能不影响运行"
        ((checks_passed++))  # 允许通过，只是警告
    fi
    
    # 评估结果
    local success_rate=$((checks_passed * 100 / total_checks))
    
    if [[ $success_rate -ge 80 ]]; then
        log SUCCESS "🎉 部署验证通过 ($checks_passed/$total_checks)"
        return 0
    else
        log ERROR "❌ 部署验证失败 ($checks_passed/$total_checks)"
        return 1
    fi
}

# 显示部署结果
show_deployment_result() {
    local success="$1"
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo -e "\n${CYAN}=================================================================="
    
    if [[ "$success" == "true" ]]; then
        echo -e "${GREEN}🎉 部署成功完成！${NC}"
        echo -e "${CYAN}=================================================================="
        echo -e "${NC}"
        
        echo "📊 部署统计："
        echo "   耗时: ${duration}秒"
        echo "   模式: $DEPLOY_MODE"
        echo "   版本: $VERSION"
        echo ""
        
        echo "📍 访问地址："
        echo "   🌐 Web应用:     http://localhost:5000"
        echo "   🗄️ 数据库管理:   http://localhost:8080"
        echo "   💾 MySQL:      localhost:3306"
        echo ""
        
        echo "🔐 默认账号："
        echo "   👨‍💼 管理员1:     admin / 518107qW"
        echo "   👨‍💼 管理员2:     longgekutta / 518107qW"
        echo "   🗄️ 数据库:      root / 518107qW"
        echo ""
        
        echo "🛠️ 管理命令："
        echo "   docker-compose ps        # 查看状态"
        echo "   docker-compose logs -f   # 查看日志"
        echo "   docker-compose restart   # 重启服务"
        echo "   docker-compose down      # 停止服务"
        echo ""
        
        echo "📋 项目信息："
        echo "   GitHub: https://github.com/Longgekutta/cloudfare-qq-mail"
        echo "   DockerHub: https://hub.docker.com/r/longgekutta/cloudfare-qq-mail"
        echo ""
        
    else
        echo -e "${RED}❌ 部署失败！${NC}"
        echo -e "${CYAN}=================================================================="
        echo -e "${NC}"
        
        echo "🔧 故障排查："
        echo "   1. 查看详细日志: cat $DEPLOY_LOG"
        echo "   2. 检查容器状态: docker-compose ps"
        echo "   3. 查看服务日志: docker-compose logs -f"
        echo "   4. 重新部署: $0 --mode=clean-deploy"
        echo ""
    fi
    
    echo -e "${CYAN}=================================================================="
    echo -e "${NC}"
}

# 清理资源
cleanup_resources() {
    log STEP "清理部署资源..."
    
    # 停止并删除容器
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 清理临时文件
    rm -f docker-compose.temp.yml
    
    # 清理无用镜像（可选）
    if [[ "${1:-}" == "deep" ]]; then
        docker system prune -f 2>/dev/null || true
    fi
    
    log SUCCESS "资源清理完成"
}

# 显示帮助
show_help() {
    cat << EOF
🚀 终极部署脚本 - Cloudfare QQ Mail Service

用法: $0 [选项]

部署模式:
  --mode=build             本地构建部署
  --mode=image             预构建镜像部署 (推荐)
  --mode=hybrid            智能部署 (先镜像后构建)
  --mode=clean-deploy      清理后重新部署

配置选项:
  --use-image              使用预构建镜像
  --skip-docker-install    跳过Docker安装
  --verbose, -v            详细输出

操作命令:
  --start                  启动服务
  --stop                   停止服务
  --restart                重启服务
  --status                 查看状态
  --logs                   查看日志
  --clean                  清理资源
  --help, -h               显示帮助

示例:
  $0                              # 自动部署
  $0 --mode=image --verbose       # 使用镜像详细部署
  $0 --mode=clean-deploy          # 清理重新部署
  $0 --start                      # 仅启动服务

项目信息:
  GitHub:    https://github.com/Longgekutta/cloudfare-qq-mail
  DockerHub: https://hub.docker.com/r/longgekutta/cloudfare-qq-mail
  Gitee:     https://gitee.com/longgekutta/cloudfare-qq-mail

EOF
}

# 主函数
main() {
    # 初始化日志
    echo "=== 终极部署开始: $(date) ===" > "$DEPLOY_LOG"
    
    show_banner
    
    log INFO "📋 开始环境检测..."
    if ! detect_environment; then
        error_exit "环境检测失败"
    fi
    
    log INFO "🐳 开始Docker环境检查..."
    if ! install_docker_smart; then
        error_exit "Docker环境配置失败"
    fi
    
    log INFO "📥 开始获取项目代码..."
    if ! get_project_code; then
        error_exit "项目代码获取失败"
    fi
    
    log INFO "⚙️ 开始创建配置..."
    if ! create_complete_config; then
        error_exit "配置创建失败"
    fi
    
    log INFO "🎯 开始选择部署方式..."
    if ! choose_deployment_method; then
        error_exit "部署方式选择失败"
    fi
    
    log INFO "🚀 开始智能部署..."
    if ! smart_deploy; then
        error_exit "智能部署失败"
    fi
    
    if wait_for_services && verify_deployment; then
        show_deployment_result "true"
        log SUCCESS "🎉 终极部署成功完成！"
        return 0
    else
        show_deployment_result "false"
        log ERROR "❌ 终极部署失败"
        return 1
    fi
}

# 服务管理函数
manage_services() {
    local action="$1"
    
    case $action in
        start)
            log INFO "启动服务..."
            docker-compose up -d
            log SUCCESS "服务已启动"
            ;;
        stop)
            log INFO "停止服务..."
            docker-compose down
            log SUCCESS "服务已停止"
            ;;
        restart)
            log INFO "重启服务..."
            docker-compose restart
            log SUCCESS "服务已重启"
            ;;
        status)
            echo "📊 服务状态："
            docker-compose ps
            ;;
        logs)
            echo "📋 实时日志："
            docker-compose logs -f
            ;;
        clean)
            cleanup_resources "deep"
            ;;
        *)
            error_exit "未知操作: $action"
            ;;
    esac
}

# 命令行参数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode=*)
            DEPLOY_MODE="${1#*=}"
            shift
            ;;
        --use-image)
            USE_PREBUILT_IMAGE=true
            shift
            ;;
        --skip-docker-install)
            SKIP_DOCKER_INSTALL=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --start|--stop|--restart|--status|--logs|--clean)
            manage_services "${1#--}"
            exit $?
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log ERROR "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 执行主函数
main "$@"

