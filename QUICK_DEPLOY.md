# 🚀 邮箱服务系统 - 超简单部署指南

## 📋 三种部署方式（任选一种）

### 方式一：GitHub源码部署（推荐）

#### Linux/macOS用户：
```bash
# 1. 克隆项目
git clone https://github.com/your-username/cloudfare-qq-mail.git
cd cloudfare-qq-mail

# 2. 一键部署
chmod +x docker-deploy.sh
./docker-deploy.sh

# 3. 访问系统
# http://localhost:5000
```

#### Windows用户：
```cmd
# 1. 克隆项目
git clone https://github.com/your-username/cloudfare-qq-mail.git
cd cloudfare-qq-mail

# 2. 一键部署
docker-deploy.bat

# 3. 访问系统
# http://localhost:5000
```

---

### 方式二：Docker Hub镜像部署（最简单）

#### 一条命令部署：
```bash
# 创建数据目录
mkdir -p cloudfare-qq-mail-data

# 一键启动（Linux/macOS）
docker run -d \
  -p 5000:5000 \
  -p 3306:3306 \
  -p 8080:8080 \
  -v $PWD/cloudfare-qq-mail-data/uploads:/app/uploads \
  -v $PWD/cloudfare-qq-mail-data/temp_attachments:/app/temp_attachments \
  -v $PWD/cloudfare-qq-mail-data/received_emails:/app/received_emails \
  --name cloudfare-qq-mail \
  your-username/cloudfare-qq-mail:latest
```

#### Windows用户：
```cmd
# 创建数据目录
mkdir cloudfare-qq-mail-data

# 一键启动
docker run -d -p 5000:5000 -p 3306:3306 -p 8080:8080 -v %cd%/cloudfare-qq-mail-data/uploads:/app/uploads -v %cd%/cloudfare-qq-mail-data/temp_attachments:/app/temp_attachments -v %cd%/cloudfare-qq-mail-data/received_emails:/app/received_emails --name cloudfare-qq-mail your-username/cloudfare-qq-mail:latest
```

---

### 方式三：Docker Compose部署（传统方式）

```bash
# 1. 获取项目文件
git clone https://github.com/your-username/cloudfare-qq-mail.git
cd cloudfare-qq-mail

# 2. 直接启动
docker-compose up -d --build

# 3. 访问系统
# http://localhost:5000
```

---

## 🎯 部署后访问信息

### 📍 访问地址：
- **Web应用**: http://localhost:5000
- **数据库管理**: http://localhost:8080  
- **MySQL数据库**: localhost:3306

### 🔐 默认账号：
- **管理员1**: admin / 518107qW
- **管理员2**: longgekutta / 518107qW
- **数据库**: root / 518107qW

---

## 🛠️ 常用管理命令

### 查看服务状态：
```bash
docker-compose ps
# 或
docker ps
```

### 查看日志：
```bash
docker-compose logs -f
# 或
docker logs cloudfare-qq-mail
```

### 停止服务：
```bash
docker-compose down
# 或
docker stop cloudfare-qq-mail
```

### 重启服务：
```bash
docker-compose restart
# 或
docker restart cloudfare-qq-mail
```

### 备份数据库：
```bash
docker-compose exec db mysqldump -u root -p518107qW cloudfare_qq_mail > backup.sql
```

---

## 🔧 服务器部署（生产环境）

### 1. 准备服务器
- Ubuntu 20.04+ / CentOS 7+
- 2GB+ 内存，20GB+ 存储
- 安装Docker和Docker Compose

### 2. 安装Docker（一键脚本）
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. 安装Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. 部署项目
```bash
cd /opt
git clone https://github.com/your-username/cloudfare-qq-mail.git
cd cloudfare-qq-mail
chmod +x docker-deploy.sh
./docker-deploy.sh
```

### 5. 配置防火墙
```bash
sudo ufw allow 5000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 6. 配置域名（可选）
```bash
# 安装Nginx
sudo apt install nginx -y

# 配置反向代理
sudo nano /etc/nginx/sites-available/cloudfare-qq-mail
```

---

## ❓ 常见问题

### Q: 端口被占用怎么办？
A: 修改docker-compose.yml中的端口映射：
```yaml
ports:
  - "8000:5000"  # 改为8000端口
```

### Q: 数据库连接失败？
A: 等待30秒让数据库完全启动，或重启服务：
```bash
docker-compose restart
```

### Q: 忘记管理员密码？
A: 默认账号是 admin/518107qW 和 longgekutta/518107qW

### Q: 如何更新系统？
A: 重新拉取代码并重新部署：
```bash
git pull origin main
docker-compose up -d --build
```

---

## 🎉 部署成功！

现在你可以：
1. 访问 http://localhost:5000 使用系统
2. 用管理员账号登录管理
3. 开始使用邮箱服务功能

**🚀 享受你的邮箱服务系统吧！**
