# 智能邮箱监控系统（cloudfare-qq-mail）

QQ 邮箱监控 + Web 管理 + 会员计费 + 邮件收发的一体化系统，面向特定域名（如 `shiep.edu.kg`）提供邮箱分配与邮件管理服务。

## 功能

- **邮件监控**：QQ 邮箱 IMAP 实时监控 → 自动下载/解析 → 存库 + 生成 HTML
- **Web 管理**：收件箱、发件箱、写邮件、回复/转发、按域名过滤
- **账号体系**：注册码注册 + 用户隔离 + 邮箱绑定（前 5 个免费、超额收费）
- **会员计费**：易支付 / 微信 / 支付宝，邮件发送按条计费
- **邮件发送**：走 Resend API

## 目录结构

```
app.py                     Flask Web 入口
main.py / auto_email_processor.py / qq_email_monitor.py / realtime_monitor.py
                           邮件监控与处理
email_sender.py            发送（Resend）      email_parser.py  解析
email_config.py / config.py  配置               email_cost_handler.py  计费
payment_monitor.py         支付监控             yipay_*.py  易支付
database/                  建表 SQL + db_manager.py
frontend/                  HTML 模板 + 静态资源
docs/                      各类功能/部署文档
scripts/                   启动、部署、维护脚本
assets/                    图片与截图
```

## 快速开始

```bash
# 1. 准备环境变量（密钥已从代码移除，必须用 .env 提供）
cp .env.example .env   # 填入真实 QQ 邮箱、数据库、Resend、易支付配置

# 2. Docker 一键起
docker-compose up -d

# 或手动运行
pip install -r requirements.txt
python app.py
```

访问 `http://localhost:5000`。

## 环境变量

所有敏感配置走 `.env`（已 gitignore），模板见 `.env.example`：

| 变量 | 说明 |
|------|------|
| `QQ_EMAIL` / `QQ_AUTH_CODE` | 被监控的 QQ 邮箱 + IMAP 授权码 |
| `DB_*` | MySQL 连接 |
| `RESEND_API_KEY` | 邮件发送（Resend） |
| `YIPAY_PID` / `YIPAY_KEY` | 易支付 |
| `SECRET_KEY` | Flask 会话密钥 |
| `TARGET_DOMAIN` | 服务的目标域名 |

## 注意

- 密钥**不要提交到仓库**；历史版本中的硬编码密钥已在此次清理中移除。
- 邮件转发依赖 Resend：`RESEND_API_KEY` 需有效，且发件域名已在 Resend 后台验证，否则转发会失败。
