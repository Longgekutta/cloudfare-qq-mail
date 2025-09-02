#!/bin/bash
# 本地验证脚本 - 在部署前验证配置

echo "🔍 开始验证配置..."

# 检查必需文件
echo "📁 检查必需文件..."
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-init.sh"
    ".env.production"
    "requirements.txt"
    "app.py"
    "database/init.sql"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    else
        echo "✅ $file"
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ 缺少必需文件: ${missing_files[*]}"
    exit 1
fi

# 检查Docker配置
echo "🐳 验证Docker配置..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml 配置正确"
else
    echo "❌ docker-compose.yml 配置有误"
    exit 1
fi

# 验证Dockerfile语法
echo "📦 验证Dockerfile..."
if docker build --dry-run . > /dev/null 2>&1; then
    echo "✅ Dockerfile 语法正确"
else
    echo "❌ Dockerfile 有语法错误"
    exit 1
fi

# 检查权限
echo "🔐 检查脚本权限..."
if [ -x "docker-init.sh" ]; then
    echo "✅ docker-init.sh 可执行"
else
    chmod +x docker-init.sh
    echo "✅ 已设置 docker-init.sh 执行权限"
fi

echo "🎉 所有验证通过！配置文件准备完毕。"
echo "📋 下一步: 将项目文件上传到服务器并运行 auto-deploy.sh"