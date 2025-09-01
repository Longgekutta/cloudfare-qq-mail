# 🚀 新服务器完整部署指南

## 📋 部署前准备清单

### 服务器要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **磁盘**: 20GB以上 SSD
- **网络**: 公网IP，开放端口 80, 443, 5000

### 必需软件
- Docker 20.0+
- Docker Compose 2.0+
- Git
- 域名（可选，用于HTTPS）

## 🔧 步骤1：服务器初始化

### 1.1 更新系统
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 1.2 安装基础工具
```bash
# Ubuntu/Debian
sudo apt install -y curl wget git vim ufw

# CentOS/RHEL
sudo yum install -y curl wget git vim firewalld
```

### 1.3 配置防火墙
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5000
sudo ufw enable

# CentOS/RHEL (Firewalld)
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## 🐳 步骤2：安装Docker

### 2.1 安装Docker
```bash
# 官方安装脚本（推荐）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加用户到docker组
sudo usermod -aG docker $USER

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
```

### 2.2 安装Docker Compose
```bash
# 下载最新版本
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

## 📥 步骤3：获取项目代码

### 3.1 克隆项目
```bash
# 克隆到服务器
git clone <项目仓库地址> /opt/cloudfare-qq-mail
cd /opt/cloudfare-qq-mail

# 设置权限
sudo chown -R $USER:$USER /opt/cloudfare-qq-mail
```

### 3.2 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

**重要配置项**：
```bash
# 数据库配置
DB_PASSWORD=your_secure_password_here
DB_NAME=cloudfare_qq_mail

# Flask配置
SECRET_KEY=your_very_secure_secret_key_here
FLASK_ENV=production

# 邮箱配置
QQ_EMAIL=your_email@qq.com
QQ_AUTH_CODE=your_qq_auth_code

# 域名配置
TARGET_DOMAIN=your-domain.com
DOMAIN=https://your-domain.com

# 端口配置（如有冲突可修改）
WEB_PORT=5000
DB_PORT=3306
PHPMYADMIN_PORT=8080

# 支付配置
YIPAY_PID=your_yipay_pid
YIPAY_KEY=your_yipay_key
YIPAY_GATEWAY=https://pay.yzhifupay.com/

# 邮件发送配置
RESEND_API_KEY=your_resend_api_key
```

## 🚀 步骤4：部署应用

### 4.1 生产环境部署
```bash
# 使用生产环境配置
chmod +x deploy-prod.sh
./deploy-prod.sh
```

### 4.2 手动部署（如脚本失败）
```bash
# 构建并启动服务
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 4.3 验证部署
```bash
# 检查容器状态
docker ps

# 测试Web应用
curl -f http://localhost:5000/

# 检查数据库连接
docker-compose -f docker-compose.prod.yml exec db mysql -u root -p -e "SHOW DATABASES;"
```

## 🌐 步骤5：配置域名和HTTPS（可选）

### 5.1 配置Nginx反向代理
```bash
# 启动Nginx容器
docker-compose -f docker-compose.prod.yml --profile nginx up -d nginx
```

### 5.2 配置SSL证书
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 5.3 更新Nginx配置
编辑 `nginx/nginx.conf` 启用HTTPS配置块。

## 📊 步骤6：系统监控和维护

### 6.1 设置日志轮转
```bash
# 创建日志轮转配置
sudo vim /etc/logrotate.d/docker-containers

# 添加配置：
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

### 6.2 设置系统监控
```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 创建监控脚本
cat > /opt/cloudfare-qq-mail/monitor.sh << 'EOF'
#!/bin/bash
echo "=== 系统状态 $(date) ==="
echo "容器状态:"
docker-compose -f /opt/cloudfare-qq-mail/docker-compose.prod.yml ps
echo "系统资源:"
free -h
df -h
echo "网络连接:"
ss -tuln | grep -E ':(80|443|5000|3306)'
EOF

chmod +x /opt/cloudfare-qq-mail/monitor.sh
```

### 6.3 设置自动备份
```bash
# 创建备份脚本
cat > /opt/cloudfare-qq-mail/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/cloudfare-qq-mail"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose -f /opt/cloudfare-qq-mail/docker-compose.prod.yml exec -T db mysqldump -u root -p$DB_PASSWORD cloudfare_qq_mail > $BACKUP_DIR/db_$DATE.sql

# 备份文件
tar -czf $BACKUP_DIR/files_$DATE.tar.gz -C /opt/cloudfare-qq-mail uploads received_emails temp_attachments

# 清理7天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
EOF

chmod +x /opt/cloudfare-qq-mail/backup.sh

# 设置定时备份
crontab -e
# 添加：每天凌晨2点备份
# 0 2 * * * /opt/cloudfare-qq-mail/backup.sh >> /var/log/backup.log 2>&1
```

## 🔧 步骤7：性能优化

### 7.1 Docker优化
```bash
# 配置Docker daemon
sudo vim /etc/docker/daemon.json

# 添加配置：
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}

# 重启Docker
sudo systemctl restart docker
```

### 7.2 系统优化
```bash
# 优化内核参数
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'net.core.somaxconn=65535' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 🚨 故障排除

### 常见问题解决

1. **容器启动失败**
   ```bash
   # 查看详细日志
   docker-compose -f docker-compose.prod.yml logs web
   
   # 检查端口占用
   sudo netstat -tlnp | grep :5000
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库容器
   docker-compose -f docker-compose.prod.yml exec db mysql -u root -p
   
   # 重置数据库密码
   docker-compose -f docker-compose.prod.yml exec db mysql -u root -p -e "ALTER USER 'root'@'%' IDENTIFIED BY 'new_password';"
   ```

3. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   docker stats
   
   # 清理Docker缓存
   docker system prune -a
   ```

## ✅ 部署完成检查清单

- [ ] 服务器基础环境配置完成
- [ ] Docker和Docker Compose安装成功
- [ ] 项目代码克隆完成
- [ ] 环境变量配置正确
- [ ] 容器成功启动
- [ ] Web应用可正常访问
- [ ] 数据库连接正常
- [ ] 邮件功能测试通过
- [ ] 支付功能配置完成
- [ ] 域名和SSL配置（如需要）
- [ ] 监控和备份脚本设置
- [ ] 防火墙规则配置正确

## 🎉 部署成功

恭喜！您已成功在新服务器上部署了邮箱监控系统。

**访问地址**: http://your-server-ip:5000 或 https://your-domain.com
**管理员账号**: admin / 518107qW

**下一步**:
1. 修改默认管理员密码
2. 配置邮箱和支付参数
3. 测试所有功能
4. 设置定期维护计划
