# 🚀 服务器部署完整指南

## 📋 项目获取方案

### 方案一：GitHub仓库部署（推荐）

#### 1.1 创建GitHub仓库
```bash
# 在本地项目目录执行
git init
git add .
git commit -m "Initial commit"

# 在GitHub创建仓库后
git remote add origin https://github.com/your-username/cloudfare-qq-mail.git
git push -u origin main
```

#### 1.2 服务器获取项目
```bash
# 在服务器上执行
cd /opt
git clone https://github.com/your-username/cloudfare-qq-mail.git
cd cloudfare-qq-mail
```

**优势**：
- ✅ 版本控制，便于更新
- ✅ 代码安全备份
- ✅ 团队协作方便
- ✅ 自动化部署支持

---

### 方案二：直接文件传输

#### 2.1 使用SCP传输
```bash
# 压缩项目文件
tar -czf cloudfare-qq-mail.tar.gz ./cloudfare-qq-mail/

# 传输到服务器
scp cloudfare-qq-mail.tar.gz root@your-server-ip:/opt/

# 在服务器上解压
ssh root@your-server-ip
cd /opt
tar -xzf cloudfare-qq-mail.tar.gz
```

#### 2.2 使用SFTP工具
- **WinSCP** (Windows)
- **FileZilla** (跨平台)
- **Cyberduck** (Mac)

**步骤**：
1. 连接到服务器
2. 上传整个项目文件夹到 `/opt/`
3. 设置正确的文件权限

---

### 方案三：Docker Hub镜像（最简单）

#### 3.1 构建并推送镜像
```bash
# 本地构建镜像
docker build -t your-username/cloudfare-qq-mail:latest .

# 推送到Docker Hub
docker push your-username/cloudfare-qq-mail:latest
```

#### 3.2 服务器拉取镜像
```bash
# 在服务器上直接运行
docker run -d \
  --name cloudfare-qq-mail \
  -p 5000:5000 \
  -e DB_HOST=your-db-host \
  -e DB_PASSWORD=518107qW \
  your-username/cloudfare-qq-mail:latest
```

**优势**：
- ✅ 最简单的部署方式
- ✅ 环境完全一致
- ✅ 一条命令即可部署

---

## 🔧 Docker部署详细步骤

### 第一步：准备服务器

#### 1.1 系统要求
- Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- 2GB+ 内存，20GB+ 存储
- 开放端口：80, 443, 5000, 3306, 8080

#### 1.2 安装Docker
```bash
# 一键安装脚本
curl -fsSL https://get.docker.com | sh

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 第二步：获取项目文件

选择上述任一方案获取项目文件到服务器的 `/opt/cloudfare-qq-mail/` 目录。

### 第三步：配置环境

#### 3.1 检查配置文件
```bash
cd /opt/cloudfare-qq-mail
ls -la

# 应该看到以下关键文件：
# - docker-compose.yml
# - Dockerfile
# - database/init.sql
# - deploy.sh
```

#### 3.2 修改配置（可选）
```bash
# 如果需要修改端口或密码
nano docker-compose.yml
```

### 第四步：一键部署

#### 4.1 使用部署脚本
```bash
# 给脚本执行权限
chmod +x deploy.sh

# 启动所有服务
./deploy.sh start
```

#### 4.2 手动部署
```bash
# 创建必要目录
mkdir -p uploads temp_attachments received_emails

# 启动服务
docker-compose up -d --build
```

### 第五步：验证部署

#### 5.1 检查服务状态
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f web
```

#### 5.2 测试访问
```bash
# 测试本地访问
curl http://localhost:5000

# 测试外网访问
curl http://your-server-ip:5000
```

### 第六步：配置域名和SSL

#### 6.1 配置Nginx反向代理
```bash
# 安装Nginx
sudo apt install nginx -y

# 创建配置
sudo nano /etc/nginx/sites-available/cloudfare-qq-mail
```

配置内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 6.2 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/cloudfare-qq-mail /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6.3 配置SSL证书
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com
```

---

## 🎯 关键问题解答

### Q1: Docker部署后数据库会自动创建吗？

**答案：是的！** 

我已经在代码中添加了自动数据库初始化功能：

1. **Docker启动时**：
   - MySQL容器会自动执行 `database/init.sql`
   - 创建所有必要的表和索引
   - 插入两个管理员账号（admin和longgekutta）

2. **应用启动时**：
   - 检查数据库是否已初始化
   - 如果是空数据库，自动执行初始化脚本
   - 确保管理员账号存在

3. **一键启动兼容**：
   - Docker环境和本地环境都支持
   - 自动检测运行环境
   - 统一的初始化流程

### Q2: 如何获取Docker打包的项目？

**三种方案**：

1. **GitHub方案**（推荐）：
   ```bash
   git clone https://github.com/your-username/cloudfare-qq-mail.git
   ```

2. **Docker Hub方案**（最简单）：
   ```bash
   docker pull your-username/cloudfare-qq-mail:latest
   ```

3. **直接传输方案**：
   - 使用SCP、SFTP等工具上传文件

### Q3: 部署后能直接使用吗？

**答案：是的！**

部署完成后：
- ✅ 数据库自动创建和初始化
- ✅ 管理员账号自动创建
- ✅ 所有表结构自动建立
- ✅ 直接访问 `http://your-domain.com` 即可使用
- ✅ 使用 `admin/518107qW` 或 `longgekutta/518107qW` 登录

---

## 🔒 安全配置

### 部署后必做事项：

1. **修改默认密码**
2. **配置防火墙**
3. **启用SSL证书**
4. **设置定期备份**
5. **监控系统日志**

---

## 📞 技术支持

如遇问题，请检查：
1. Docker服务是否正常运行
2. 端口是否被占用
3. 防火墙是否正确配置
4. 域名DNS是否正确解析

**🎉 恭喜！按照此指南，您的邮箱系统将在服务器上完美运行！**
