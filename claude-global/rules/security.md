# 安全规则

## 文件保护

**IMPORTANT**: 以下文件禁止直接修改，需要明确用户确认：

- `.env` / `.env.*` - 环境变量文件
- `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` - 依赖锁文件
- `*.pem` / `*.key` - 证书和密钥
- `credentials.*` / `secrets.*` - 凭证文件

## 敏感信息

- 凭证存放位置：`~/.claude/secrets.env`
- **YOU MUST NOT** 在代码或配置文件中硬编码 API 密钥
- 使用环境变量引用敏感信息

## Telegram 权限

Telegram 聊天能力是 CEO 助理的专属能力，其他 Agent 禁止使用。
