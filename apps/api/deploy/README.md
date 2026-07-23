# 吾食（Wushi）后端 · 腾讯云 SCF 部署手册

将 `apps/api`（FastAPI 后端）部署为**腾讯云 SCF 容器镜像 Web 函数**，前端经 API 网关访问 `/api/*`。

> ⚠️ 本手册对应的命令**未在当前环境执行**（无腾讯云凭证、未连接连接器、且避免消耗资源）。
> 请在你自己的腾讯云账号下按以下步骤操作。

## 前置条件

- 腾讯云账号，并已开通：容器镜像服务（TCR）、云函数 SCF、API 网关。
- 本地已安装 Docker，且能登录 `ccr.ccs.tencentyun.com`。
- 一个可用的 PostgreSQL 实例（生产库；本地验证可用 SQLite，但生产必须用 PostgreSQL）。
- Serverless Framework（用于 `serverless.yml` 一键部署，可选）。

## ① 构建镜像

```bash
cd apps/api
docker build -t wushi-api .
```

本地可快速自测（用 SQLite 验证镜像可启动）：

```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=sqlite+aiosqlite:///./dev.db \
  -e JWT_SECRET=dev-secret \
  wushi-api
curl http://localhost:8000/health
# -> {"status":"ok"}
```

## ② 推送镜像到 TCR

```bash
# 登录（使用你自己的腾讯云账号 / 命名空间）
docker login ccr.ccs.tencentyun.com

# 打 tag（将 <namespace> 替换为你的 TCR 命名空间）
docker tag wushi-api:latest ccr.ccs.tencentyun.com/<namespace>/wushi-api:latest

# 推送
docker push ccr.ccs.tencentyun.com/<namespace>/wushi-api:latest
```

> 推送后，请将 `deploy/serverless.yml` 中的 `image` 字段替换为上述完整地址。

## ③ 创建 SCF 容器镜像 Web 函数

- 在 SCF 控制台创建「**容器镜像**」函数（Web 函数类型）。
- 选择 ② 中推送的镜像。
- **监听端口**：镜像内 gunicorn 已读取环境变量 `${PORT:-8000}`（见 `Dockerfile`）。
  腾讯云容器镜像 Web 函数默认注入 `PORT=9000`，平台将流量转发到该端口，二者天然一致；
  若你更希望固定 8000，也可在函数配置里把「容器端口」显式设为 8000（二者二选一，避免 9000↔8000 不匹配导致收不到请求）。
- 绑定 API 网关，生成对外 HTTP 地址。

> 本地调试：未注入 `PORT` 时自动回退 8000，可直接 `docker run -p 8000:8000 ...` 后用 `curl http://localhost:8000/health` 验证。

## ④ 配置环境变量

在函数「环境变量」中设置（**密钥切勿写死进镜像或提交到仓库**）：

| 变量 | 说明 | 示例 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 异步连接串（生产必填） | `postgresql+asyncpg://user:pass@host:5432/wushi` |
| `DEEPSEEK_API_KEY` | DeepSeek key；留空则自动回退模板 | ``（空） |
| `JWT_SECRET` | JWT 签名密钥，生产务必用强随机值 | `****` |
| `CORS_ORIGINS` | 逗号分隔的允许来源 | `https://your.domain` 或 `*` |

数据库迁移（首次部署后）：

```bash
# 对生产库执行 Alembic 迁移（可在本地对生产库执行，或在函数内执行）
alembic upgrade head
```

## ⑤ 健康检查

```bash
curl https://<你的API网关地址>/health
# -> {"status":"ok"}
```

## ⑥ （可选）Serverless Framework 一键部署

```bash
cd apps/api/deploy
# 先安装并配置腾讯云密钥
npm i -g serverless
serverless deploy
```

`serverless.yml` 已定义 Web 函数 `wushi-api`（region `ap-guangzhou`，可改区）、
API 网关 HTTP 触发（根路径 `/` 代理 `/api/*`）与占位环境变量，请替换其中的镜像地址与密钥后再部署。

## 关键注意事项

- 本部署套件**未实际执行** `docker build` / `push` / `serverless deploy`（当前环境无腾讯云凭证）。
- 生产必须使用 **PostgreSQL**，由 `DATABASE_URL` 提供；SQLite 仅用于本地验证。
- 所有密钥经环境变量注入，镜像内不含任何真实凭据。
- `requirements.txt` 未包含 gunicorn，已在 `Dockerfile` 中一并安装（详见 Dockerfile 备注）。
