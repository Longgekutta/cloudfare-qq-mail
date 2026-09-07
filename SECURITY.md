# 安全配置说明

## 会话 Cookie 安全

- `SESSION_COOKIE_HTTPONLY=True`：禁止 JavaScript 读取会话 Cookie，降低 XSS 后会话窃取风险。
- `SESSION_COOKIE_SAMESITE='Lax'`：限制跨站携带 Cookie，降低 CSRF 风险。
- `SESSION_COOKIE_SECURE`：仅在显式设置环境变量 `SESSION_COOKIE_SECURE=true` 时启用，要求 Cookie 仅通过 HTTPS 传输。
- `PERMANENT_SESSION_LIFETIME`：会话最长有效期为 24 小时。

## 基础安全响应头

- `X-Content-Type-Options: nosniff`：禁止浏览器猜测 MIME 类型。
- `X-Frame-Options: SAMEORIGIN`：仅允许同源嵌入页面，降低点击劫持风险。
- `Referrer-Policy: strict-origin-when-cross-origin`：控制 Referer 信息泄露。
- `Permissions-Policy`：关闭不必要的浏览器能力。
