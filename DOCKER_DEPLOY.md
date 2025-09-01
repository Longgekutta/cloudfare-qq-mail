# 邮箱服务 Docker 容器化部署指南

## 📋 概述

本指南将帮助您使用Docker容器化部署邮箱服务系统，实现一键部署、环境隔离和便捷管理。

## 🎯 Docker部署的优势

### 1. **环境一致性**
- 开发、测试、生产环境完全一致
- 消除"在我机器上能运行"的问题
- 标准化的运行环境

### 2. **简化部署**
- 一条命令即可部署整个应用栈
- 自动处理依赖关系
- 无需手动配置环境

### 3. **资源隔离**
- 每个服务独立运行
- 避免端口冲突和依赖冲突
- 更好的安全性

### 4. **易于扩展**
- 可以轻松创建多个实例
- 支持负载均衡
- 便于水平扩展

## 🛠️ 部署前准备

### 1. 安装Docker

#### Windows系统：
1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 启动Docker Desktop
3. 确保Docker正在运行

#### Linux系统：
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 验证安装
```bash
docker --version
docker-compose --version
```

## 🚀 快速部署

### Windows用户：
```cmd
# 启动服务
deploy.bat start

# 查看状态
deploy.bat status

# 查看日志
deploy.bat logs

# 停止服务
deploy.bat stop
```

### Linux/Mac用户：
```bash
# 给脚本执行权限
chmod +x deploy.sh

# 启动服务
./deploy.sh start

# 查看状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 停止服务
./deploy.sh stop
```

### 手动部署：
```bash
# 创建必要目录
mkdir -p uploads temp_attachments received_emails

# 构建并启动服务
docker-compose up -d --build

# 查看运行状态
docker-compose ps
```

## 📊 服务架构

### 容器服务说明：

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| web | cloudfare-qq-mail-web | 5000 | Flask Web应用 |
| db | cloudfare-qq-mail-db | 3306 | MySQL数据库 |
| phpmyadmin | cloudfare-qq-mail-phpmyadmin | 8080 | 数据库管理界面 |

### 访问地址：
- **Web应用**: http://localhost:5000
- **数据库管理**: http://localhost:8080
- **MySQL数据库**: localhost:3306

### 默认账号：
- **管理员账号**: admin / admin123
- **数据库**: root / 518107qW

## 🔧 配置说明

### 环境变量配置：
```yaml
environment:
  - DB_HOST=db                    # 数据库主机
  - DB_USER=root                  # 数据库用户
  - DB_PASSWORD=518107qW          # 数据库密码
  - DB_NAME=cloudfare_qq_mail     # 数据库名称
  - FLASK_ENV=production          # Flask环境
```

### 数据持久化：
```yaml
volumes:
  - ./uploads:/app/uploads                    # 上传文件
  - ./temp_attachments:/app/temp_attachments  # 临时附件
  - ./received_emails:/app/received_emails    # 接收邮件
  - mysql_data:/var/lib/mysql                 # 数据库数据
```

## 📋 常用命令

### 服务管理：
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps
```

### 容器管理：
```bash
# 进入Web容器
docker-compose exec web bash

# 进入数据库容器
docker-compose exec db mysql -u root -p

# 查看容器资源使用
docker stats
```

### 数据管理：
```bash
# 备份数据库
docker-compose exec db mysqldump -u root -p518107qW cloudfare_qq_mail > backup.sql

# 恢复数据库
docker-compose exec -T db mysql -u root -p518107qW cloudfare_qq_mail < backup.sql

# 清理未使用的资源
docker system prune -f
```

## 🔍 故障排除

### 1. 端口冲突
如果端口被占用，修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "5001:5000"  # 将5000改为5001
```

### 2. 数据库连接失败
检查数据库容器是否正常启动：
```bash
docker-compose logs db
```

### 3. 权限问题
确保目录权限正确：
```bash
chmod 755 uploads temp_attachments received_emails
```

### 4. 内存不足
增加Docker Desktop的内存限制，或清理不用的容器：
```bash
docker system prune -a
```

## 🔒 安全建议

### 1. 修改默认密码
部署后立即修改：
- 管理员账号密码
- 数据库root密码

### 2. 网络安全
- 使用防火墙限制端口访问
- 配置HTTPS证书
- 定期更新容器镜像

### 3. 数据备份
- 定期备份数据库
- 备份重要配置文件
- 测试恢复流程

## 📈 性能优化

### 1. 资源限制
在 `docker-compose.yml` 中添加资源限制：
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

### 2. 日志管理
配置日志轮转：
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🎯 生产环境部署

### 1. 使用外部数据库
```yaml
environment:
  - DB_HOST=your-mysql-server.com
  - DB_USER=your-username
  - DB_PASSWORD=your-password
```

### 2. 配置反向代理
使用Nginx作为反向代理：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 监控和日志
- 配置日志收集系统
- 设置监控告警
- 定期健康检查

## 📞 技术支持

如果在部署过程中遇到问题：

1. 查看容器日志：`docker-compose logs`
2. 检查容器状态：`docker-compose ps`
3. 验证网络连接：`docker network ls`
4. 检查资源使用：`docker stats`

## 🌐 服务器部署详细步骤

### 第一步：准备服务器环境

#### 1.1 服务器要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **内存**: 最少2GB，推荐4GB+
- **存储**: 最少20GB可用空间
- **网络**: 公网IP，开放80、443、5000端口

#### 1.2 连接到服务器
```bash
# 使用SSH连接到服务器
ssh root@your-server-ip

# 或使用密钥连接
ssh -i your-key.pem root@your-server-ip
```

**原理说明**: SSH是安全的远程连接协议，通过加密通道管理服务器。

### 第二步：安装Docker环境

#### 2.1 更新系统包
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

**原理说明**: 更新系统包确保安全补丁和最新功能可用。

#### 2.2 安装Docker
```bash
# 下载Docker安装脚本
curl -fsSL https://get.docker.com -o get-docker.sh

# 执行安装
sudo sh get-docker.sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
```

**原理说明**: Docker提供容器化环境，确保应用在不同服务器上运行一致。

#### 2.3 安装Docker Compose
```bash
# 下载Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

**原理说明**: Docker Compose管理多容器应用，简化服务编排和部署。

### 第三步：上传项目文件

#### 3.1 方法一：使用SCP上传
```bash
# 在本地电脑上执行
scp -r ./cloudfare-qq-mail root@your-server-ip:/opt/

# 如果使用密钥
scp -i your-key.pem -r ./cloudfare-qq-mail root@your-server-ip:/opt/
```

#### 3.2 方法二：使用Git克隆
```bash
# 在服务器上执行
cd /opt
git clone https://github.com/your-username/cloudfare-qq-mail.git
```

#### 3.3 方法三：使用SFTP工具
- 使用WinSCP (Windows)
- 使用FileZilla (跨平台)
- 使用Cyberduck (Mac)

**原理说明**: 将本地代码传输到服务器，为部署做准备。

### 第四步：配置环境

#### 4.1 进入项目目录
```bash
cd /opt/cloudfare-qq-mail
```

#### 4.2 检查配置文件
```bash
# 查看Docker配置
cat docker-compose.yml

# 查看Dockerfile
cat Dockerfile
```

#### 4.3 修改配置（如需要）
```bash
# 编辑docker-compose.yml
nano docker-compose.yml

# 修改端口映射（如果5000端口被占用）
ports:
  - "8080:5000"  # 外部8080端口映射到容器5000端口
```

**原理说明**: 根据服务器环境调整配置，避免端口冲突。

### 第五步：部署应用

#### 5.1 使用部署脚本（推荐）
```bash
# 给脚本执行权限
chmod +x deploy.sh

# 启动服务
./deploy.sh start
```

#### 5.2 手动部署
```bash
# 创建必要目录
mkdir -p uploads temp_attachments received_emails

# 构建并启动服务
docker-compose up -d --build

# 查看启动状态
docker-compose ps
```

**原理说明**:
- `--build`: 重新构建镜像，确保使用最新代码
- `-d`: 后台运行，不占用终端
- `docker-compose ps`: 查看容器运行状态

#### 5.3 验证部署
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f web

# 测试网络连接
curl http://localhost:5000
```

### 第六步：配置防火墙和域名

#### 6.1 配置防火墙
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

**原理说明**: 防火墙控制网络访问，只开放必要端口确保安全。

#### 6.2 配置Nginx反向代理（可选但推荐）
```bash
# 安装Nginx
sudo apt install nginx -y

# 创建配置文件
sudo nano /etc/nginx/sites-available/cloudfare-qq-mail
```

Nginx配置内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/cloudfare-qq-mail /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

**原理说明**: Nginx作为反向代理，提供更好的性能、SSL支持和负载均衡。

#### 6.3 配置SSL证书（推荐）
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
0 12 * * * /usr/bin/certbot renew --quiet
```

**原理说明**: SSL证书加密网络传输，保护用户数据安全。

### 第七步：监控和维护

#### 7.1 查看运行状态
```bash
# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats

# 查看日志
docker-compose logs -f
```

#### 7.2 备份数据
```bash
# 备份数据库
docker-compose exec db mysqldump -u root -p518107qW cloudfare_qq_mail > backup_$(date +%Y%m%d).sql

# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/ temp_attachments/ received_emails/
```

#### 7.3 更新应用
```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose up -d --build

# 清理旧镜像
docker system prune -f
```

### 第八步：故障排除

#### 8.1 常见问题

**问题1: 端口被占用**
```bash
# 查看端口占用
sudo netstat -tlnp | grep :5000

# 杀死占用进程
sudo kill -9 PID
```

**问题2: 数据库连接失败**
```bash
# 查看数据库容器日志
docker-compose logs db

# 重启数据库容器
docker-compose restart db
```

**问题3: 内存不足**
```bash
# 查看内存使用
free -h

# 清理Docker资源
docker system prune -a
```

#### 8.2 性能优化

**优化1: 增加内存限制**
在docker-compose.yml中添加：
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

**优化2: 配置日志轮转**
```yaml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 🎯 部署检查清单

部署完成后，请检查以下项目：

- [ ] 容器正常运行 (`docker-compose ps`)
- [ ] 网站可以访问 (`curl http://your-domain.com`)
- [ ] 数据库连接正常
- [ ] 管理员账号可以登录 (admin/admin123)
- [ ] 邮件发送功能正常
- [ ] SSL证书配置正确（如果使用）
- [ ] 防火墙规则正确
- [ ] 备份策略已设置

### 🔒 安全建议

1. **修改默认密码**: 立即修改admin账号和数据库密码
2. **定期更新**: 保持系统和Docker镜像更新
3. **监控日志**: 定期检查应用和系统日志
4. **备份数据**: 设置自动备份策略
5. **限制访问**: 使用防火墙限制不必要的端口访问

---

**🎉 恭喜！您已成功部署邮箱服务系统到服务器！**

现在您可以通过 http://your-domain.com 访问系统，使用 admin/admin123 登录管理界面。
