# 📧 CloudFlare QQ 邮箱监控系统

智能邮箱监控系统：QQ 邮箱邮件监控 + 自动处理 + Web 管理后台 + 易支付/注册码商业化功能。

> **项目背景（2026-07 构建）**: 在 CloudFlare 服务器上部署的邮箱自动化系统，
> 解决"监控指定邮箱 → 自动处理邮件 → 支持付费开通"的完整闭环。

## 一、这是什么（30 秒看懂）

```
QQ邮箱 ──监控──▶ 本系统 (Flask) ──▶ 自动处理
   ▲                                │
   │                                ▼
 邮件到达                      Web 管理后台 (5000)
   │                          (收件箱/用户管理/支付)
   │                                │
   └──────── 邮件转发/附件处理 ◀────┘
```

**核心能力：**
- 📥 **QQ 邮箱实时监控** — 定时拉取指定邮箱，新邮件自动入库
- 🤖 **自动处理** — 关键词过滤、域名过滤、附件保存、自动回复转发
- 💰 **商业化** — 易支付集成（支付宝/微信）、注册码系统、用户权限管理
- 🌐 **Web 后台** — Flask 管理界面，邮箱/用户/支付/系统配置可视化

## 二、快速部署

### 方式 A：Docker 一键部署（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
#    编辑 .env: QQ_EMAIL / QQ_AUTH_CODE / DB 配置 / YIPAY 配置

# 2. 启动
./docker-deploy.sh          # Linux/macOS
# 或 docker-deploy.bat      # Windows

# 3. 访问
# 系统后台:  http://localhost:5000
# 数据库:    http://localhost:8080 (phpMyAdmin)
```

### 方式 B：源码运行

```bash
pip install -r requirements.txt
python3 app.py              # 主应用
python3 auto_email_processor.py   # 邮件监控进程 (独立跑)
```

> 📋 更多部署细节（Docker Compose / 腾讯云 / 多容器）见：
> - `QUICK_DEPLOY.md` — 三种部署方式速查
> - `SERVER_DEPLOYMENT_GUIDE.md` — 服务器完整部署
> - `docs/DEPLOYMENT_GUIDE.md` — 部署决策记录

## 三、项目结构

```
cloudfare-qq-mail/
├── app.py                     # Flask 主应用 (Web 后台)
├── main.py                    # 入口聚合
├── auto_email_processor.py    # 邮件自动处理进程
├── qq_email_monitor.py        # QQ 邮箱监控器
├── realtime_monitor.py        # 实时监控
├── email_parser.py            # 邮件解析
├── email_sender.py            # 邮件发送
├── email_cost_handler.py      # 邮件成本控制
├── component_connector.py     # 组件连接器
├── config.py                  # 系统配置
├── yipay_config.py            # 易支付配置
├── yipay_utils.py             # 易支付工具
├── payment_monitor.py         # 支付监控
├── database/
│   ├── db_manager.py          # 数据库连接池管理
│   ├── create_tables.sql      # 建表脚本
│   └── *.sql                  # 增量表/字段脚本
├── frontend/
│   ├── templates/             # Jinja2 模板
│   └── static/                # 静态资源
├── docs/                      # 详细文档
│   ├── DEPLOYMENT_GUIDE.md    # 部署指南
│   ├── TECHNICAL_GUIDE.md     # 技术架构
│   └── USER_GUIDE.md          # 用户手册
├── nginx/                     # Nginx 配置
├── .env.example               # 环境变量模板
└── Dockerfile*                # 多环境 Dockerfile
```

## 四、核心配置 (.env)

| 变量 | 说明 |
|---|---|
| `QQ_EMAIL` / `QQ_AUTH_CODE` | QQ 邮箱地址 + 授权码（非密码！） |
| `DB_HOST/USER/PASSWORD/NAME` | MySQL 数据库 |
| `SECRET_KEY` | Flask 密钥（生产必改） |
| `RESEND_API_KEY` | Resend 邮件发送 API |
| `YIPAY_PID` / `YIPAY_KEY` | 易支付商户号 + 密钥 |
| `WEB_PORT` | Web 端口（默认 5000） |

## 五、文档导航

| 文档 | 内容 |
|---|---|
| `QUICK_DEPLOY.md` | ⚡ 三种部署方式（源码/Docker Hub/Compose） |
| `SERVER_DEPLOYMENT_GUIDE.md` | 🖥️ 服务器完整部署指南 |
| `DOCKER_DEPLOY.md` | 🐳 Docker 部署详解 |
| `docs/TECHNICAL_GUIDE.md` | 🔧 技术架构说明 |
| `docs/USER_GUIDE.md` | 👤 用户使用手册 |
| `docs/DEPLOYMENT_GUIDE.md` | 📐 部署决策与方案对比 |
| `数据库设计文档.md` | 🗄️ 数据库表结构 |
| `支付监控使用说明.md` | 💰 易支付/注册码使用 |
| `系统使用说明.md` | 📖 系统操作说明 |

## 六、注意事项

- ⚠️ QQ 邮箱需开启 SMTP 并获取**授权码**，不是登录密码
- ⚠️ 生产环境必须修改 `SECRET_KEY`，不要用默认值
- ⚠️ 支付功能涉及资金，上线前务必在易支付后台核对回调地址
- 📌 邮件数据/附件默认存 `uploads/` 和 `temp_attachments/`，注意备份
