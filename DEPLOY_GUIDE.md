# 🚀 一键部署指南

## 服务器要求

- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+)
- **必需软件**: Docker 和 Docker Compose
- **最小配置**: 1GB RAM, 10GB 磁盘空间

## 一键部署步骤

### 方法1: 自动部署（推荐）

只需要在服务器上执行以下 **3 个命令**：

```bash
# 1. 上传项目文件到服务器
scp -r cloudfare-qq-mail/ user@your-server:/tmp/

# 2. 登录服务器并进入项目目录
ssh user@your-server
cd /tmp/cloudfare-qq-mail

# 3. 执行一键部署脚本
chmod +x auto-deploy.sh && ./auto-deploy.sh
```

### 方法2: 手动部署（备用）

如果自动部署失败，使用以下 **5 个命令**：

```bash
# 1. 复制环境配置
cp .env.production .env

# 2. 生成密钥（可选）
sed -i "s/SECRET_KEY=.*/SECRET_KEY=cloudfare_$(date +%s)/" .env

# 3. 构建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d

# 5. 查看状态
docker-compose ps
```

## 部署后验证

✅ **服务检查**:
```bash
curl http://localhost:5000/
```

✅ **访问地址**:
- 邮箱服务: http://your-server-ip:5000
- 数据库管理: http://your-server-ip:8080

✅ **默认账号**:
- 用户名: `admin`
- 密码: `518107qW`

## 故障排查

### 如果容器启动失败：

```bash
# 查看容器状态
docker-compose ps

# 查看详细日志
docker-compose logs web
docker-compose logs db

# 重启服务
docker-compose restart
```

### 如果端口被占用：

```bash
# 修改端口配置
nano .env
# 更改 WEB_PORT=5001

# 重新启动
docker-compose down && docker-compose up -d
```

### 如果数据库连接失败：

```bash
# 检查数据库日志
docker-compose logs db

# 重置数据库
docker-compose down -v
docker-compose up -d
```

## 生产环境配置

🔐 **安全配置**:
1. 修改默认密码
2. 更新 `.env` 中的敏感信息
3. 配置防火墙规则
4. 启用 HTTPS（可选）

📧 **邮箱配置**:
1. 修改 `QQ_EMAIL` 为你的邮箱
2. 更新 `QQ_AUTH_CODE` 为你的授权码
3. 设置 `TARGET_DOMAIN` 为你的域名

💰 **支付配置**（可选）:
1. 配置 `YIPAY_PID` 和 `YIPAY_KEY`
2. 设置支付网关地址

## 技术支持

如果遇到问题，请检查：
1. Docker 和 Docker Compose 版本
2. 系统防火墙设置
3. 网络连接状态
4. 磁盘空间是否充足

---

**💡 提示**: 首次部署成功后，后续更新只需要 `git pull && docker-compose up -d --build` 即可！