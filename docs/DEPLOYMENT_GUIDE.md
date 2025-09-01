# 📦 邮箱监控系统部署指南

## 🎯 概述

本指南提供了邮箱监控系统的完整部署方案，包括本地部署、Docker容器化部署和服务器部署。

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web应用容器    │    │   数据库容器     │    │   反向代理       │
│   (Flask App)   │◄──►│   (MySQL 8.0)   │    │   (可选)        │
│   端口: 5000     │    │   端口: 3306     │    │   端口: 80/443   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速部署 (推荐)

### 方式一：Docker Compose 一键部署

1. **环境要求**
   - Docker 20.0+
   - Docker Compose 2.0+
   - 2GB+ 可用内存
   - 5GB+ 可用磁盘空间

2. **部署步骤**
   ```bash
   # 克隆项目
   git clone <项目地址>
   cd cloudfare-qq-mail
   
   # 一键部署
   docker-compose up -d --build
   ```

3. **访问系统**
   - Web界面: http://localhost:5000
   - 数据库管理: http://localhost:8080 (phpMyAdmin)
   - 默认管理员: admin / admin123

### 方式二：Windows 批处理部署

```batch
# 运行部署脚本
docker-deploy.bat
```

### 方式三：Linux/Mac 脚本部署

```bash
# 给脚本执行权限
chmod +x docker-deploy.sh

# 运行部署脚本
./docker-deploy.sh
```

## 🔧 手动部署

### 环境要求

- **操作系统**: Windows 10+, Ubuntu 18.04+, CentOS 7+
- **Python**: 3.7+
- **数据库**: MySQL 5.7+ 或 MySQL 8.0
- **内存**: 最低 1GB，推荐 2GB+
- **磁盘**: 最低 2GB，推荐 10GB+

### 安装步骤

1. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置数据库**
   ```bash
   # 创建数据库
   mysql -u root -p
   CREATE DATABASE cloudfare_qq_mail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   # 初始化表结构
   python database/setup_database.py
   ```

3. **配置邮件服务**
   编辑 `email_config.py`:
   ```python
   QQ_EMAIL = "your_email@qq.com"
   QQ_AUTH_CODE = "your_auth_code"
   DB_PASSWORD = "your_db_password"
   ```

4. **启动系统**
   ```bash
   # 方式一：统一启动器 (推荐)
   python 启动邮件系统.py
   
   # 方式二：手动启动各组件
   python app.py                    # Web应用
   python component_connector.py    # 邮件处理
   python start_monitor.py          # 邮件监控
   ```

## 🐳 Docker 部署详解

### 容器服务说明

1. **Web应用容器** (`cloudfare-qq-mail-web`)
   - 基础镜像: python:3.9-slim
   - 端口映射: 5000:5000
   - 功能: Flask Web应用、邮件处理

2. **数据库容器** (`cloudfare-qq-mail-db`)
   - 基础镜像: mysql:8.0
   - 端口映射: 3306:3306
   - 数据持久化: mysql_data 卷

3. **数据库管理** (`cloudfare-qq-mail-phpmyadmin`)
   - 基础镜像: phpmyadmin/phpmyadmin
   - 端口映射: 8080:80
   - 功能: 数据库可视化管理

### 环境变量配置

```yaml
environment:
  - DB_HOST=db
  - DB_USER=root
  - DB_PASSWORD=518107qW
  - DB_NAME=cloudfare_qq_mail
  - FLASK_ENV=production
```

### 数据卷配置

```yaml
volumes:
  - ./uploads:/app/uploads                    # 上传文件
  - ./temp_attachments:/app/temp_attachments  # 临时附件
  - ./received_emails:/app/received_emails    # 接收邮件
  - mysql_data:/var/lib/mysql                 # 数据库数据
```

## 🌐 服务器部署

### 1. 云服务器准备

**推荐配置**:
- CPU: 2核心+
- 内存: 4GB+
- 磁盘: 20GB+ SSD
- 带宽: 5Mbps+

**支持的云平台**:
- 阿里云ECS
- 腾讯云CVM
- AWS EC2
- Azure VM

### 2. 安全配置

```bash
# 防火墙配置
ufw allow 22      # SSH
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw allow 5000    # 应用端口
ufw enable

# SSL证书配置 (可选)
certbot --nginx -d your-domain.com
```

### 3. 反向代理配置 (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 进程管理 (Systemd)

创建服务文件 `/etc/systemd/system/cloudfare-mail.service`:

```ini
[Unit]
Description=Cloudfare QQ Mail System
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/cloudfare-qq-mail
ExecStart=/usr/bin/python3 启动邮件系统.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
systemctl enable cloudfare-mail
systemctl start cloudfare-mail
systemctl status cloudfare-mail
```

## 📊 监控和维护

### 1. 日志管理

```bash
# Docker日志
docker-compose logs -f

# 系统日志
journalctl -u cloudfare-mail -f

# 应用日志
tail -f logs/app.log
```

### 2. 数据备份

```bash
# 数据库备份
docker-compose exec db mysqldump -u root -p518107qW cloudfare_qq_mail > backup_$(date +%Y%m%d).sql

# 文件备份
tar -czf backup_files_$(date +%Y%m%d).tar.gz uploads received_emails
```

### 3. 性能监控

```bash
# 容器资源使用
docker stats

# 系统资源监控
htop
df -h
free -h
```

## 🔍 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :5000
   
   # 修改端口映射
   # 编辑 docker-compose.yml
   ports:
     - "5001:5000"  # 改为5001
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose exec db mysql -u root -p518107qW -e "SHOW DATABASES;"
   
   # 重启数据库
   docker-compose restart db
   ```

3. **邮件监控异常**
   ```bash
   # 检查邮件配置
   python -c "from email_config import *; print(f'邮箱: {QQ_EMAIL}')"
   
   # 测试IMAP连接
   python -c "import imaplib; imaplib.IMAP4_SSL('imap.qq.com', 993)"
   ```

### 日志分析

```bash
# 查看错误日志
docker-compose logs web | grep ERROR

# 查看数据库日志
docker-compose logs db | grep ERROR

# 实时监控日志
docker-compose logs -f --tail=100
```

## 📋 部署检查清单

### 部署前检查
- [ ] Docker和Docker Compose已安装
- [ ] 端口5000、3306、8080未被占用
- [ ] 磁盘空间充足 (>5GB)
- [ ] 网络连接正常

### 部署后验证
- [ ] Web界面可正常访问 (http://localhost:5000)
- [ ] 用户可正常登录注册
- [ ] 邮件监控功能正常
- [ ] 数据库连接正常
- [ ] 文件上传下载正常

### 生产环境检查
- [ ] SSL证书配置完成
- [ ] 防火墙规则设置正确
- [ ] 数据备份策略已制定
- [ ] 监控告警已配置
- [ ] 日志轮转已设置

## 🎉 部署完成

恭喜！您已成功部署邮箱监控系统。

**下一步操作**:
1. 访问 http://your-domain.com 或 http://localhost:5000
2. 使用管理员账号登录 (admin / admin123)
3. 配置域名和用户权限
4. 开始使用邮件监控功能

**获取帮助**:
- 查看系统使用说明: `docs/USER_GUIDE.md`
- 查看API文档: `docs/API_REFERENCE.md`
- 问题反馈: 提交Issue到项目仓库
