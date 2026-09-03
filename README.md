# 智能邮箱监控系统（cloudfare-qq-mail）

QQ 邮箱监控 + Web 管理 + 会员计费 + 邮件收发的一体化系统，面向特定域名（如 `shiep.edu.kg`）提供邮箱分配与邮件管理服务。

## 功能

- **邮件监控**：QQ 邮箱 IMAP 实时监控 → 自动下载/解析 → 存库 + 生成 HTML 预览
- **Web 管理**：收件箱、发件箱、写邮件、回复/转发、按域名过滤、附件管理
- **账号体系**：注册码注册 + 用户隔离 + 邮箱绑定（前 5 个免费、超额收费）
- **会员计费**：易支付 / 微信 / 支付宝，邮件发送按条计费，VIP 享免费额度
- **邮件发送**：走 Resend API，支持自定义发件域名

## 目录结构

```
app.py                     Flask Web 基础入口
app_with_isolation.py      Flask Web 入口（带用户隔离，推荐生产使用）
main.py / auto_email_processor.py / qq_email_monitor.py / realtime_monitor.py
                           邮件监控与处理（自动下载、解析、入库）
email_sender.py            邮件发送（Resend API）      email_parser.py  邮件解析
email_config.py / config.py  系统配置（环境变量读取 + 业务参数）
email_cost_handler.py      邮件计费逻辑
payment_monitor.py         支付回调监控                 yipay_*.py  易支付集成
database/                  建表 SQL + 数据库管理模块
frontend/                  HTML 模板 + 静态资源
docs/                      详细功能/部署/使用文档
scripts/                   启动、部署、维护脚本
assets/                    图片与截图资源
```

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone <仓库地址>
cd cloudfare-qq-mail

# 2. 准备环境变量
cp .env.example .env   # 填入真实 QQ 邮箱、数据库、Resend、SECRET_KEY 等配置

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库（首次部署必须执行，否则服务无法正常运行）
# 方式A：直接导入 SQL 到数据库容器
docker exec -i $(docker-compose ps -q db) mysql -u$DB_USER -p$DB_PASSWORD $DB_NAME < database/init.sql
# 方式B：在 Web 容器内执行初始化脚本
docker exec -it $(docker-compose ps -q web) python database/setup_database.py
```

访问 `http://localhost:5000` 即可使用。

### 方式二：手动部署

```bash
# 1. 克隆仓库并安装依赖
git clone <仓库地址>
cd cloudfare-qq-mail
pip install -r requirements.txt

# 2. 准备环境变量
cp .env.example .env   # 填入所有必要配置（见下方环境变量说明）

# 3. 初始化数据库（首次部署必须执行）
# 方式A：直接导入 SQL 到 MySQL
mysql -u your_user -p your_database < database/init.sql
# 方式B：运行初始化脚本（需提前在 .env 中配置数据库连接）
python database/setup_database.py

# 4. 启动 Web 服务（推荐使用带用户隔离的版本）
python app_with_isolation.py
# 或基础版（无用户隔离，仅供测试）
# python app.py

# 5. 启动邮件监控（必须，否则无法自动收取邮件，建议用后台运行/守护进程）
python auto_email_processor.py
# 或使用集成启动脚本
# python scripts/启动邮件系统.py

# 6. （可选）启动支付监控（如需使用充值/会员功能）
python payment_monitor.py
```

访问 `http://localhost:5000` 即可使用。

## 环境变量

所有敏感配置走 `.env`（已 gitignore），模板见 `.env.example`，**带 ✅ 为必填项**：

| 变量 | 说明 | 必填 |
|------|------|------|
| `SECRET_KEY` | Flask 会话密钥，建议使用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成 | ✅ |
| `QQ_EMAIL` | 被监控的 QQ 邮箱地址 | ✅ |
| `QQ_AUTH_CODE` | QQ 邮箱 IMAP 授权码（需在 QQ 邮箱设置中开启 IMAP 服务） | ✅ |
| `DB_HOST` | MySQL 数据库地址 | ✅ |
| `DB_PORT` | MySQL 数据库端口（默认 3306） | ✅ |
| `DB_USER` | MySQL 用户名 | ✅ |
| `DB_PASSWORD` | MySQL 密码 | ✅ |
| `DB_NAME` | MySQL 数据库名 | ✅ |
| `RESEND_API_KEY` | Resend API Key，需提前在 Resend 后台验证发件域名 | ✅ |
| `TARGET_DOMAIN` | 服务的目标域名（如 `shiep.edu.kg`），用于邮箱绑定过滤 | ✅ |
| `YIPAY_PID` | 易支付商户 ID（如需支付/充值功能） | ⭕ |
| `YIPAY_KEY` | 易支付商户密钥（如需支付/充值功能） | ⭕ |
| 其他可选变量 | 见 `.env.example` 内注释 | ⭕ |

## 注意事项

- 🔐 **密钥安全**：所有敏感配置务必通过 `.env` 提供，**绝对不要提交到 Git 仓库**；历史版本中的硬编码密钥已全部清理。
- 📧 **邮件发送**：邮件转发/发送依赖 Resend API，`RESEND_API_KEY` 需有效，且发件域名已在 Resend 后台完成 SPF/DKIM 验证，否则发送会失败。
- 👤 **用户隔离**：生产环境请务必使用 `app_with_isolation.py` 启动 Web 服务，确保不同用户仅能访问自己的邮件与绑定邮箱，避免数据泄露。
- 📥 **邮件监控**：仅启动 Web 服务无法自动收取邮件，需同时运行 `auto_email_processor.py`（或对应监控脚本），建议配置为系统服务或守护进程。
- 💳 **支付功能**：如需使用会员/充值功能，需配置易支付（或其他支付渠道）并启动 `payment_monitor.py` 处理支付回调。
- 🗄️ **数据库**：首次部署必须执行数据库初始化，否则所有功能都会报错；建议定期备份数据库数据。
- 📖 **更多文档**：详细的部署、功能、使用说明请查看 `docs/` 目录下的对应文档，包含部署指南、用户手册、技术说明等。
- ⚠️ **临时密钥提示**：若未配置 `SECRET_KEY`，系统会自动生成临时密钥，重启后所有用户会话会失效，生产环境务必配置固定的 `SECRET_KEY`。