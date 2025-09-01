#!/bin/bash

# 邮箱服务Docker一键部署脚本
# 参考咸鱼自动回复项目的部署方式

set -e

PROJECT_NAME="cloudfare-qq-mail"
IMAGE_NAME="cloudfare-qq-mail"
VERSION="1.0"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_banner() {
    echo "=================================================================="
    echo "📧 邮箱服务系统 - Docker一键部署"
    echo "=================================================================="
    echo "🕐 部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "📁 工作目录: $(pwd)"
    echo "=================================================================="
}

check_docker() {
    print_message $BLUE "🔍 检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        print_message $RED "❌ Docker未安装，请先安装Docker"
        echo "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    print_message $GREEN "✅ Docker环境检查通过"
}

create_directories() {
    print_message $BLUE "📁 创建必要目录..."
    
    mkdir -p uploads
    mkdir -p temp_attachments  
    mkdir -p received_emails
    mkdir -p mysql_data
    
    print_message $GREEN "✅ 目录创建完成"
}

deploy_services() {
    print_message $BLUE "🚀 开始部署服务..."
    
    # 构建并启动服务
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ 服务部署成功！"
        
        print_message $YELLOW "📍 访问地址："
        print_message $YELLOW "  - Web应用: http://localhost:5000"
        print_message $YELLOW "  - 数据库管理: http://localhost:8080"
        print_message $YELLOW "  - MySQL: localhost:3306"
        
        print_message $YELLOW "🔐 默认账号："
        print_message $YELLOW "  - 管理员1: admin / 518107qW"
        print_message $YELLOW "  - 管理员2: longgekutta / 518107qW"
        print_message $YELLOW "  - 数据库: root / 518107qW"
        
    else
        print_message $RED "❌ 服务部署失败"
        exit 1
    fi
}

wait_for_services() {
    print_message $BLUE "⏳ 等待服务启动..."
    
    # 等待Web服务启动
    for i in {1..30}; do
        if curl -s http://localhost:5000 > /dev/null 2>&1; then
            print_message $GREEN "✅ Web服务已启动"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_message $YELLOW "⚠️ Web服务启动较慢，请稍后手动检查"
        fi
        
        sleep 2
    done
}

show_status() {
    print_message $BLUE "📊 服务状态："
    docker-compose ps
    
    print_message $BLUE "🔍 容器详细信息："
    docker ps --filter "name=${PROJECT_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

main() {
    print_banner
    check_docker
    create_directories
    deploy_services
    wait_for_services
    show_status
    
    print_message $GREEN "🎉 部署完成！"
    print_message $BLUE "💡 使用说明："
    print_message $BLUE "  - 查看日志: docker-compose logs -f"
    print_message $BLUE "  - 停止服务: docker-compose down"
    print_message $BLUE "  - 重启服务: docker-compose restart"
    print_message $BLUE "  - 备份数据: ./deploy.sh backup"
}

# 处理命令行参数
case "${1:-deploy}" in
    deploy)
        main
        ;;
    stop)
        print_message $BLUE "🛑 停止服务..."
        docker-compose down
        print_message $GREEN "✅ 服务已停止"
        ;;
    restart)
        print_message $BLUE "🔄 重启服务..."
        docker-compose down
        main
        ;;
    status)
        show_status
        ;;
    logs)
        docker-compose logs -f
        ;;
    backup)
        print_message $BLUE "💾 备份数据库..."
        timestamp=$(date +"%Y%m%d_%H%M%S")
        backup_file="backup_${timestamp}.sql"
        docker-compose exec db mysqldump -u root -p518107qW cloudfare_qq_mail > $backup_file
        print_message $GREEN "✅ 数据库备份完成: $backup_file"
        ;;
    help|--help|-h)
        echo "邮箱服务Docker部署脚本"
        echo ""
        echo "使用方法:"
        echo "  $0 [命令]"
        echo ""
        echo "可用命令:"
        echo "  deploy    部署服务（默认）"
        echo "  stop      停止服务"
        echo "  restart   重启服务"
        echo "  status    查看状态"
        echo "  logs      查看日志"
        echo "  backup    备份数据库"
        echo "  help      显示帮助"
        ;;
    *)
        print_message $RED "❌ 未知命令: $1"
        print_message $BLUE "使用 $0 help 查看帮助"
        exit 1
        ;;
esac
