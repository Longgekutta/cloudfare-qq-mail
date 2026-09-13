#!/bin/bash
# 调试部署脚本 - 快速诊断容器启动问题

echo "🔍 调试部署问题 - 详细诊断"
echo "=================================="

# 检查是否在项目目录中
if [[ -f "app.py" && -f "docker-compose.yml" ]] || [[ -f "app.py" && -f "docker-compose.tencent.yml" ]]; then
    echo "✅ 已在项目目录中: $(pwd)"
elif [[ -d "app-cloudfare-qq-mail" ]]; then
    cd cloudfare-qq-mail
    echo "✅ 进入项目目录: $(pwd)"
else
    echo "❌ 未找到项目文件，请确保在正确的目录中"
    echo "当前目录: $(pwd)"
    echo "目录内容: $(ls -la)"
    exit 1
fi

# 检查Docker镜像是否构建成功
echo ""
echo "🐳 检查Docker镜像："
if docker images | grep -E "(cloudfare-qq-mail|tencent)" | head -5; then
    echo "✅ 找到相关镜像"
else
    echo "❌ 没有找到构建的镜像"
fi

echo ""
echo "📋 检查docker-compose文件："
compose_file="docker-compose.tencent.yml"
if [[ -f "$compose_file" ]]; then
    echo "✅ $compose_file 存在"
else
    compose_file="docker-compose.yml"
    echo "⚠️ 使用默认 $compose_file"
fi

# 停止所有服务
echo ""
echo "🛑 停止所有服务..."
docker-compose -f "$compose_file" down --remove-orphans 2>/dev/null || true
docker-compose down --remove-orphans 2>/dev/null || true

# 清理悬空镜像和容器
echo "🧹 清理资源..."
docker system prune -f >/dev/null 2>&1 || true

# 检查端口占用
echo ""
echo "🔍 检查端口占用："
for port in 5000 3306 8080; do
    if netstat -tuln 2>/dev/null | grep ":$port " >/dev/null; then
        echo "⚠️ 端口 $port 被占用："
        netstat -tulpn 2>/dev/null | grep ":$port " || echo "   详情未知"
        
        # 尝试杀掉占用进程
        pid=$(lsof -ti:$port 2>/dev/null || netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
        if [[ -n "$pid" && "$pid" != "-" ]]; then
            echo "   尝试释放端口..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    else
        echo "✅ 端口 $port 可用"
    fi
done

# 检查.env文件
echo ""
echo "⚙️ 检查配置文件："
if [[ -f ".env" ]]; then
    echo "✅ .env 文件存在"
    echo "   关键配置："
    grep -E "^(DB_|WEB_PORT|SECRET_KEY)" .env | head -5 || echo "   配置文件可能有问题"
else
    echo "❌ .env 文件不存在，创建默认配置..."
    if [[ -f ".env.production" ]]; then
        cp .env.production .env
        echo "✅ 从 .env.production 复制配置"
    else
        echo "❌ .env.production 也不存在"
    fi
fi

# 尝试单独启动数据库
echo ""
echo "🗄️ 尝试单独启动数据库..."
docker-compose -f "$compose_file" up -d db

echo "⏳ 等待数据库启动 (15秒)..."
sleep 15

echo "📊 数据库状态："
docker-compose -f "$compose_file" ps db

# 检查数据库日志
echo ""
echo "📋 数据库启动日志："
docker-compose -f "$compose_file" logs --tail=10 db

# 测试数据库连接
echo ""
echo "🔗 测试数据库连接："
if docker-compose -f "$compose_file" exec -T db mysqladmin ping -h localhost -u root -p518107qW 2>/dev/null; then
    echo "✅ 数据库连接成功"
else
    echo "❌ 数据库连接失败"
    echo "数据库详细日志："
    docker-compose -f "$compose_file" logs --tail=20 db
fi

# 尝试启动Web服务
echo ""
echo "🌐 尝试启动Web服务..."
docker-compose -f "$compose_file" up -d web

echo "⏳ 等待Web服务启动 (10秒)..."
sleep 10

echo "📊 Web服务状态："
docker-compose -f "$compose_file" ps web

echo ""
echo "📋 Web服务日志："
docker-compose -f "$compose_file" logs --tail=15 web

# 最终状态检查
echo ""
echo "🎯 最终状态："
echo "--- 所有容器状态 ---"
docker-compose -f "$compose_file" ps

echo ""
echo "--- 端口监听状态 ---"
netstat -tuln 2>/dev/null | grep -E ':(5000|3306|8080)' || echo "相关端口未监听"

# 测试服务
echo ""
echo "🧪 服务测试："
if curl -s --connect-timeout 5 http://localhost:5000 >/dev/null 2>&1; then
    echo "✅ Web服务响应正常"
    echo "🎉 部署成功！访问地址: http://localhost:5000"
else
    echo "❌ Web服务无响应"
    
    echo ""
    echo "🔧 建议的修复步骤："
    echo "1. 检查容器是否正常运行："
    echo "   docker-compose -f $compose_file ps"
    echo ""
    echo "2. 查看详细日志："
    echo "   docker-compose -f $compose_file logs -f web"
    echo ""
    echo "3. 进入容器检查："
    echo "   docker-compose -f $compose_file exec web bash"
    echo ""
    echo "4. 重新构建："
    echo "   docker-compose -f $compose_file up -d --build --force-recreate"
fi

echo ""
echo "=================================="
echo "调试完成"
