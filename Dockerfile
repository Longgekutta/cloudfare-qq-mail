# 使用Python官方镜像
FROM python:3.9-slim

# 设置标签信息
LABEL maintainer="cloudfare-qq-mail"
LABEL version="1.0.0"
LABEL description="Cloudfare QQ Mail Service"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 设置工作目录
WORKDIR /app

# 创建非root用户（安全性考虑）
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    default-mysql-client \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件并安装Python依赖
COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用文件（分层复制以优化缓存）
COPY app.py config.py ./
COPY *.py ./
COPY database/ ./database/
COPY frontend/ ./frontend/
COPY nginx/ ./nginx/

# 复制所有脚本和配置文件
COPY *.sh ./
COPY *.bat ./
COPY docker-compose*.yml ./
COPY .env.production ./.env

# 创建必要的目录并设置权限
RUN mkdir -p /app/uploads /app/temp_attachments /app/received_emails /app/sent_attachments /app/logs /app/database/backup && \
    chmod 755 /app/uploads /app/temp_attachments /app/received_emails /app/sent_attachments /app/logs /app/database/backup

# 确保脚本可执行
RUN chmod +x /app/docker-init.sh && \
    chmod +x /app/*.sh 2>/dev/null || true && \
    chmod +x /app/super-deploy.sh 2>/dev/null || true

# 验证关键文件存在并显示详细信息
RUN echo "=== 验证应用文件 ===" && \
    ls -la /app/ && \
    echo "=== 验证数据库文件 ===" && \
    ls -la /app/database/ && \
    echo "=== 验证关键文件 ===" && \
    test -f /app/app.py && echo "✅ app.py 存在" && \
    test -f /app/config.py && echo "✅ config.py 存在" && \
    test -f /app/database/init.sql && echo "✅ init.sql 存在" && \
    test -f /app/docker-init.sh && echo "✅ docker-init.sh 存在" && \
    test -f /app/.env && echo "✅ .env 存在" && \
    echo "🎉 所有关键文件验证完成"

# 创建环境文件的备份
RUN cp /app/.env /app/.env.backup || echo "环境文件备份创建"

# 设置文件所有权
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:5000/ || exit 1

# 启动命令
CMD ["/app/docker-init.sh"]
