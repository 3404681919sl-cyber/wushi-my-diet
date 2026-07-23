# 吾食（my diet）

> 边吃边学：把多种疾病互相矛盾的饮食禁忌，磨合成一份「能吃什么、能吃多少」的个性化、可量化方案。

当饮食建议本身在互相矛盾时，最困难的不是缺少选择，而是缺少一个能分辨"对你而言此刻何为适合"的方法。

许多同时存在多种健康状况的人，常陷入两难：一种诉求所鼓励的食物，恰好是另一种诉求所警惕的。例如，肠易激综合征的低发漫原则会限制多种高纤蔬果与豆类，而血糖管理或体重控制的目标却往往依赖这些食材来提供营养与饱腹感。诸如此类的冲突在日常饮食中反复出现，使得单一的"忌口清单"不仅难以执行，反而容易造成不必要的饮食焦虑。

吾食正是为这类多维饮食矛盾而设计的小程序。它并非提供另一份僵化的清单，而是构建一个**个人食物耐受边界学习系统**——借助贝叶斯模型与用户自身的小剂量微挑战数据，持续标定每种食物在当前身体状况下的安全摄入阈值，并在此基础上生成真正贴合个人需求的食谱方案。

这一路径在方法上是数据驱动、可量化的，在应用前景上则兼具临床营养转化与日常健康管理的双重价值。

## 两个核心引擎

- **贝叶斯个人耐受模型** —— 小步微挑战，越用越懂你
- **DeepSeek V4 Pro** —— 自然语言食谱生成，把你的边界翻译成一日三餐

## Monorepo 结构

```
wushi/
├── apps/
│   ├── miniprogram/   # 微信小程序 + H5 同构（Taro + Vue3）
│   └── api/           # 后端服务（FastAPI + SQLAlchemy 2.0 async + Alembic）
├── packages/
│   └── shared/        # 前后端共享枚举 / 类型 / 常量
├── deploy/            # 本地 docker-compose（PostgreSQL + 可选 Redis）
└── docs/              # PRD / 系统架构设计 / 类图 / 时序图
```

## 技术栈

- **前端**：Taro 3 + Vue3 + Pinia + NutUI + ECharts（微信小程序 + H5 同构）
- **后端**：FastAPI（async）+ SQLAlchemy 2.0（async）+ Alembic + Pydantic v2
- **数据库**：PostgreSQL（主库，asyncpg 驱动）；Redis（F4 可选，本期未强制）
- **鉴权**：JWT（python-jose）+ bcrypt 密码哈希；微信登录预留 `code2session`
- **建模内核**：NumPyro（贝叶斯后验）+ 闭式 log-normal 共轭（在线更新）；DeepSeek V4 Pro 食谱生成（T3 实现）

## 阶段与任务

| 阶段 | 任务 | 状态 |
|---|---|---|
| T0 | 脚手架 / Monorepo 初始化 | ✅ 已完成 |
| T1 | 后端基础：Auth + DB 模型 + 迁移 | ✅ 已完成 |
| T2 | 贝叶斯内核 + 冲突引擎 + 组合负担 + 三色安全评估 | ✅ 已完成 |
| T3 | DeepSeek V4 Pro 食谱生成接线（LLM 优先 / 超时回退模板） | ✅ 已完成 |
| T4 | 前端页面与状态（5 页 + 组件） | ✅ 已完成 |
| T5 | 前后端联调 + H5 同构 + 手机号登录体系 | ✅ 已完成 |
| T6 | 测试（38/38 全绿）+ 腾讯云 SCF 部署物料 | ✅ 已完成 |

## 快速开始（后端）

```bash
cd apps/api

# 1. 准备虚拟环境并安装依赖
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env   # 按需修改 DATABASE_URL / JWT_SECRET 等

# 3. 启动服务（默认 SQLite 可用于本地验证；生产请改用 PostgreSQL）
uvicorn app.main:app --reload

# 4. 建表（任选其一）
#    a) Alembic 迁移（生产推荐）
alembic upgrade head
#    b) 开发兜底：直接 create_all + 种子食物
python -m app.db.init_db

# 5. 健康检查
curl http://localhost:8000/health   # -> {"status":"ok"}

# 6. 接口文档
open http://localhost:8000/docs
```

> ⚠️ 生产目标数据库为 `postgresql+asyncpg://...`。开发环境在无 Docker/PostgreSQL 时可使用
> `sqlite+aiosqlite:///./dev.db` 经 `create_all` 验证模型可创建（JSONB 在 SQLite 下自动编译为 JSON）。
> 模型未使用 PostgreSQL 专有类型之外的不可移植写法。

## 测试

```bash
cd apps/api
pytest -q   # 38 用例全绿：注册(手机号)/登录/me/食物/食谱(LLM 回退)/地图/微挑战/耐受
```

## 环境说明

- 微信类目定位：**健康 / 食品管理（非医疗诊断）**；数据上云加密 + 导出 / 删除。
- DeepSeek 超时允许模板回退，保证可用性。
- 先只做小程序（H5 同构代码保留，暂不上线）。

## 生产部署 / Deployment

后端可部署为**腾讯云 SCF 容器镜像 Web 函数 + API 网关**。完整物料与分步手册见
[`apps/api/deploy/README.md`](apps/api/deploy/README.md)，包含：

- `apps/api/Dockerfile`（基于 `python:3.11-slim`，内置 gunicorn + UvicornWorker，监听 8000）
- `apps/api/.dockerignore`
- `apps/api/deploy/serverless.yml`（Serverless Framework `tencent-scf` Web 函数定义）
- `apps/api/deploy/README.md`（构建 / 推送 TCR / 创建函数 / 配置环境变量 / 健康检查）

> 前置依赖：**PostgreSQL**（生产库，经 `DATABASE_URL` 注入）+ 你自己的**腾讯云账号与凭证**。
> 仓库内不含任何真实密钥；`DEEPSEEK_API_KEY` / `JWT_SECRET` 等均在运行时由环境变量注入。
