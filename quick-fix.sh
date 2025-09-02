#!/bin/bash
# 快速修复脚本 - 用于服务启动失败时的快速诊断和修复

echo "🔧 快速修复和诊断脚本"
echo "=================================="

# 进入项目目录
if [[ -d "cloudfare-qq-mail" ]]; then
    cd cloudfare-qq-mail
    echo "✅ 已进入项目目录"
else
    echo "❌ 项目目录不存在"
    exit 1
fi

# 1. 检查基本文件
echo ""
echo "📁 检查关键文件："
files=(".env" "docker-compose.yml" "Dockerfile" "app.py")
for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 缺失"
    fi
done

# 2. 检查Docker状态
echo ""
echo "🐳 Docker状态："
if docker info >/dev/null 2>&1; then
    echo "✅ Docker服务正常"
else
    echo "❌ Docker服务异常"
    exit 1
fi

# 3. 停止所有相关容器
echo ""
echo "🛑 停止旧容器..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose -f docker-compose.china.yml down --remove-orphans 2>/dev/null || true

# 4. 清理可能的问题
echo ""
echo "🧹 清理资源..."
docker system prune -f >/dev/null 2>&1 || true

# 5. 检查端口占用
echo ""
echo "🔍 检查端口占用："
ports=(5000 3306 8080)
for port in "${ports[@]}"; do
    if netstat -tuln 2>/dev/null | grep ":$port " >/dev/null; then
        echo "⚠️ 端口 $port 被占用"
        echo "   占用进程: $(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' || echo '未知')"
    else
        echo "✅ 端口 $port 可用"
    fi
done

# 6. 创建必要目录
echo ""
echo "📁 创建目录..."
mkdir -p uploads temp_attachments received_emails sent_attachments logs mysql_data
chmod 755 uploads temp_attachments received_emails sent_attachments logs mysql_data

# 7. 检查.env文件
echo ""
echo "⚙️ 检查配置文件..."
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.production" ]]; then
        cp .env.production .env
        echo "✅ 从.env.production复制配置文件"
    else
        echo "❌ 缺少环境配置文件"
        cat > .env << EOF
WEB_PORT=5000
DB_HOST=db
DB_PORT=3306
DB_USER=root
DB_PASSWORD=518107qW
DB_NAME=cloudfare_qq_mail
QQ_EMAIL=2846117874@qq.com
QQ_AUTH_CODE=ajqnryrvvjmsdcgi
TARGET_DOMAIN=shiep.edu.kg
RESEND_API_KEY=re_6giBFioy_HW9cYt9xfR473x39HkuKtXT5
YIPAY_PID=6166
YIPAY_KEY=deefc7cc0449be9cb621b7800f5e7f1c
YIPAY_GATEWAY=https://pay.yzhifupay.com/
SECRET_KEY=cloudfare_qq_mail_secret_key_2025
TZ=Asia/Shanghai
EOF
        echo "✅ 创建了基础配置文件"
    fi
fi

# 8. 尝试快速启动
echo ""
echo "🚀 尝试启动服务..."

# 检查是否有国内优化版本
if [[ -f "docker-compose.china.yml" ]]; then
    echo "使用国内优化版本启动..."
    docker-compose -f docker-compose.china.yml up -d --build
    compose_file="docker-compose.china.yml"
else
    echo "使用标准版本启动..."
    docker-compose up -d --build
    compose_file="docker-compose.yml"
fi

# 9. 等待并检查
echo ""
echo "⏳ 等待服务启动 (30秒)..."
sleep 30

echo ""
echo "📊 最终状态检查："
echo "--- 容器状态 ---"
docker-compose -f "$compose_file" ps

echo ""
echo "--- 服务测试 ---"
if curl -s http://localhost:5000 >/dev/null 2>&1; then
    echo "✅ Web服务响应正常"
    echo "🎉 修复成功！访问地址: http://localhost:5000"
else
    echo "❌ Web服务无响应"
    echo ""
    echo "最后的日志："
    docker-compose -f "$compose_file" logs --tail=10 web
fi

echo ""
echo "=================================="
echo "如果问题仍然存在，请运行："
echo "docker-compose -f $compose_file logs -f"
echo "查看详细日志"
