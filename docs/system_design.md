# 吾食（Wushi）系统架构设计 + 任务分解

> 版本：v1.0 · 作者：高见远（架构师） · 状态：待团队评审
> 关联：PRD v1.0（`docs/prd.md`）、已锁定技术决策
> 仓库根：`D:\projects\my\吾食-wxapp\`（monorepo，建议目录名 `wushi/`）

---

## 0. 架构选型结论速览（用于回传摘要）

| 维度 | 选型 | 一句话理由 |
|---|---|---|
| 形态 | Taro 3 + Vue3（微信小程序 + H5 同构） | 一套代码双端，符合已锁定决策 |
| 状态管理 | Pinia | Vue3 官方推荐，轻量、devtools 友好 |
| UI 组件 | NutUI（Taro 版）/ Taro UI 候选 | Taro UI 对 Vue3 支持滞后，NutUI 适配更好（保留 Taro UI 备选） |
| 图表 | ECharts（weapp 端 echarts-for-weixin，H5 端 echarts）+ 自封装 `RadarChart` | 雷达图/热力图需求确定，ECharts 跨端成熟 |
| 后端 | FastAPI（async）+ SQLAlchemy 2.0 + Alembic + Pydantic v2 | 异步高并发、类型安全、迁移成熟 |
| 数据库 | PostgreSQL（主）+ Redis（缓存/队列，可选） | PRD 锁定；Neo4j 初期降级 JSONB |
| 贝叶斯内核 | **NumPyro（Pyro 概率编程）为主，闭式共轭（log-normal 阈值模型）做 MVP 在线更新**；scikit-learn 仅作 A6 知识库辅助 | 真正输出"个性化安全剂量分布"，而非二值概率 |
| 食谱生成 | DeepSeek V4 Pro（OpenAI 兼容 SDK，`deepseek-v4-pro`）+ 模板回退 | 双内核组合，缺一不可 |
| 部署 | 腾讯云 SCF（Serverless）+ Docker，本地 docker-compose（pg+redis） | 弹性、按量、易运维 |
| 工程 | pnpm workspaces monorepo（`apps/miniprogram`、`apps/api`、`packages/shared`） | 共享类型不漂移，统一部署 |

---

## 1. 实现方案 + 框架选型

### 1.1 Monorepo 结构（确认 + 微调）

确认 PRD §0 方案，做两处微调：

1. **前端 UI 库**：PRD 写 `Taro UI`，但 Taro UI 对 Vue3 支持滞后且不活跃。建议 **NutUI（`@nutui/nutui-taro`）** 作为主 UI 库（京东开源、Taro+Vue3 一等公民支持），`taro-ui-vue3` 作为备选。下文统一以 NutUI 为例，构建可切换。
2. **后端 ORM 异步化**：采用 SQLAlchemy 2.0 **async** 引擎（`asyncpg` 驱动），与 FastAPI `async def` 路由一致，避免线程池瓶颈。开发期可用 `asyncpg` 直连；迁移用 Alembic（async env）。

其他完全遵循 PRD。包管理 `pnpm`，根 `pnpm-workspace.yaml` 声明 `apps/*`、`packages/*`。

### 1.2 前端选型与理由

- **Taro 3 + Vue3**：已锁定。Taro 3 的 Vue3 运行时成熟；用 `@tarojs/plugin-platform-weapp` + `@tarojs/plugin-platform-h5` 双端编译。
- **Pinia**：替代 Vuex，组合式 API 友好，便于在 `stores/` 中做单一数据源。
- **NutUI（Taro）**：组件齐全（滑块、步骤条、徽章、弹层），满足三色徽章、剂量滑块、微挑战步骤条等。
- **ECharts 封装**：小程序端用 `echarts-for-weixin`（按需打包 echarts 核心），H5 端用标准 `echarts`；通过一个 `RadarChart.vue` 抽象组件按 `process.env.TARO_ENV` 切换实现，对外暴露统一 props（data/options）。
- **请求层**：基于 `Taro.request` 封装 `services/http.ts`（统一 baseURL、JWT 注入、错误归一化），不引入 axios（跨端一致性更好，H5 下 Taro.request 仍可工作）。

### 1.3 后端选型与理由

- **FastAPI + Pydantic v2**：类型安全、自动 OpenAPI 文档、异步原生。
- **SQLAlchemy 2.0（async）+ Alembic**：2.0 风格（`Mapped[]`/`mapped_column`）更清晰；Alembic 管理 schema 演进。
- **鉴权**：`python-jose[cryptography]` 签发/校验 JWT；`passlib[bcrypt]`（或 `bcrypt`）仅用于本地/兜底账号。微信登录走 `core/wechat.py` 调 `code2session` 换 `openid/unionid`，绑定到 `User`。
- **HTTP 客户端**：`httpx[async]` 用于调用 DeepSeek 与微信接口。
- **缓存/队列（F4 可选）**：`redis` + `arq` 或 `rq`（异步食谱生成任务），MVP 可同步实现、留异步开关。

### 1.4 贝叶斯内核选型（重点）

**结论：选用 NumPyro（Pyro 的概率编程 NumPy 后端，基于 JAX）作为概率编程内核；MVP 的"在线后验更新"采用可解析的闭式共轭（log-normal 阈值模型），NumPyro 负责后验采样、不确定性估计与未来 SVI 联合多因素推断。scikit-learn 仅用于 A6 知识库的轻量聚类/特征标准化，不参与核心耐受推断。**

理由：
- 需求是"每食物**个性化安全剂量分布**（非二值开关）"，需要可追踪后验分布。scikit-learn 的 `GaussianNB`/`MultinomialNB` 是频率式分类器，输出类概率、无先验注入、不支持在线剂量更新，不符合。
- NumPyro/Pyro 是真正的概率编程：可定义先验、似然、做 MCMC/SVI 推断后验。选 NumPyro 而非 Pyro（PyTorch 后端）是因为 JAX 推理更快、易部署到 Serverless、无重 PyTorch 依赖。
- 但每次日志都跑 MCMC 太慢。MVP 用**对数正态剂量-阈值模型的闭式正态共轭更新**（计算 O(1)、可在线、可解释），仅在"需要不确定性可视化 / 未来多因素联合推断"时用 NumPyro 采样。这样兼顾性能与可解释性。

### 1.5 DeepSeek 接线方式

- 用 **OpenAI 兼容 SDK**（`openai` python 包或 `httpx` 直调），`base_url=https://api.deepseek.com/v1`，`model=deepseek-v4-pro`。
- 食谱生成为"约束注入 + 结构化输出"：把用户画像、三色等级、耐受阈值、目标权重、组合负担约束注入 prompt，要求返回严格 JSON（见 §9.2 schema）。
- 失败回退：超时（>8s）/ 解析失败 → 模板生成器（从 🟢 库抽 majority + 探索插入），返回带 `burden_warning="模板生成"` 的食谱。
- 成本控制：prompt 前缀缓存（相同画像）、`max_tokens` 限制、结果按"约束哈希"缓存 24h（Redis，可选）。

### 1.6 部署

- 腾讯云 **SCF（云函数）** + 自定义运行时（Docker 镜像），`deploy/scf/Dockerfile` + `serverless.yml`。
- 本地 `deploy/docker-compose.yml` 起 PostgreSQL + Redis，便于开发。
- 前端：`taro build --type weapp` 产物传微信开发者工具；H5 产物挂静态托管（SCF/cos）。

---

## 2. 文件列表及相对路径（完整目录树）

```
wushi/                                   # monorepo 根（实际落盘 D:\projects\my\吾食-wxapp\）
├── apps/
│   ├── miniprogram/                     # Taro + Vue3 小程序/H5
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── dashboard/           # 首页仪表盘
│   │   │   │   │   ├── index.vue
│   │   │   │   │   └── index.config.ts
│   │   │   │   ├── profile/            # 健康画像
│   │   │   │   │   ├── index.vue
│   │   │   │   │   └── index.config.ts
│   │   │   │   ├── challenge/          # 微挑战
│   │   │   │   │   ├── index.vue
│   │   │   │   │   └── index.config.ts
│   │   │   │   ├── recipe/             # 食谱
│   │   │   │   │   ├── index.vue
│   │   │   │   │   └── index.config.ts
│   │   │   │   └── map/                # 成长地图
│   │   │   │       ├── index.vue
│   │   │   │       └── index.config.ts
│   │   │   ├── components/
│   │   │   │   ├── SafetyBadge.vue      # 三色安全徽章 🟢🟡🔴
│   │   │   │   ├── DoseSlider.vue       # 剂量滑块
│   │   │   │   ├── RadarChart.vue        # 雷达图（ECharts 抽象）
│   │   │   │   ├── WeightSlider.vue      # 目标权重条
│   │   │   │   └── BurdenWarning.vue     # 组合负担预警条
│   │   │   ├── stores/
│   │   │   │   ├── user.ts              # 登录态/用户信息
│   │   │   │   ├── profile.ts           # 画像/状况/症状词典
│   │   │   │   ├── tolerance.ts         # 三色/耐受阈值（前端镜像计算）
│   │   │   │   └── recipe.ts            # 食谱/目标权重
│   │   │   ├── services/
│   │   │   │   ├── http.ts             # Taro.request 封装（JWT/错误归一）
│   │   │   │   ├── auth.ts
│   │   │   │   ├── profile.ts
│   │   │   │   ├── challenge.ts
│   │   │   │   ├── recipe.ts
│   │   │   │   └── map.ts
│   │   │   ├── utils/
│   │   │   │   ├── safety.ts           # 三色计算（与后端一致的规则镜像）
│   │   │   │   ├── burden.ts           # 组合负担前端预览计算
│   │   │   │   └── format.ts
│   │   │   ├── App.vue
│   │   │   ├── app.config.ts
│   │   │   └── main.ts                 # 入口（createApp + Pinia + 路由）
│   │   ├── config/
│   │   │   ├── index.ts               # 环境感知 baseURL 等
│   │   │   ├── dev.ts
│   │   │   └── prod.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── api/                             # FastAPI 后端
│       ├── app/
│       │   ├── main.py                 # 创建 app、挂载 v1 路由、CORS、异常处理器
│       │   ├── api/v1/
│       │   │   ├── auth.py             # /api/v1/auth 微信登录、JWT
│       │   │   ├── profile.py          # /api/v1/profile 状况/症状/画像
│       │   │   ├── challenge.py        # /api/v1/challenge 微挑战 CRUD + 步骤
│       │   │   ├── recipe.py           # /api/v1/recipe 食谱生成
│       │   │   └── map.py              # /api/v1/map 雷达/热力数据
│       │   ├── core/
│       │   │   ├── config.py           # pydantic-settings 读环境变量
│       │   │   ├── security.py         # JWT 签发/校验、密码哈希
│       │   │   ├── deps.py             # get_current_user、db session 依赖
│       │   │   └── wechat.py           # code2session 换 openid/unionid
│       │   ├── models/                 # SQLAlchemy 2.0 模型
│       │   │   ├── user.py
│       │   │   ├── profile.py
│       │   │   ├── condition.py
│       │   │   ├── symptom.py
│       │   │   ├── meal.py
│       │   │   ├── challenge.py
│       │   │   ├── food.py
│       │   │   └── tolerance.py
│       │   ├── schemas/                # Pydantic v2 请求/响应
│       │   │   ├── auth.py
│       │   │   ├── profile.py
│       │   │   ├── challenge.py
│       │   │   ├── recipe.py
│       │   │   └── map.py
│       │   ├── services/
│       │   │   ├── tolerance/          # 贝叶斯个人耐受模型
│       │   │   │   ├── __init__.py
│       │   │   │   ├── prior.py        # 冷启动先验（A6 知识库）
│       │   │   │   ├── update.py       # 后验更新（log-normal 共轭）
│       │   │   │   └── model.py        # NumPyro 后验采样/可视化
│       │   │   ├── conflict/           # 矛盾破解引擎
│       │   │   │   ├── __init__.py
│       │   │   │   └── engine.py       # 交集/并集/冲突标注
│       │   │   ├── recipe/             # DeepSeek 食谱生成层
│       │   │   │   ├── __init__.py
│       │   │   │   ├── prompt.py       # prompt 工程
│       │   │   │   ├── client.py       # DeepSeek client（OpenAI 兼容）
│       │   │   │   ├── schema.py       # 食谱 JSON schema 校验
│       │   │   │   └── fallback.py     # 模板回退生成
│       │   │   └── burden/             # 组合负担计算
│       │   │       ├── __init__.py
│       │   │       ├── fodmap.py       # FODMAP 六类总量
│       │   │       └── gl.py           # 血糖负荷 GL
│       │   └── db/
│       │       ├── base.py             # Base、async engine
│       │       ├── session.py          # async_session 工厂
│       │       └── migrations/         # Alembic
│       │           ├── env.py
│       │           ├── script.py.mako
│       │           └── versions/
│       ├── tests/
│       │   ├── test_auth.py
│       │   ├── test_tolerance.py
│       │   ├── test_recipe.py
│       │   └── test_burden.py
│       ├── pyproject.toml
│       ├── requirements.txt
│       └── alembic.ini
├── packages/
│   └── shared/                          # 前后端共享常量/枚举/类型
│       ├── src/
│       │   ├── enums.ts                # SafetyLevel / SymptomType / FodmapCategory / GoalType
│       │   ├── types.ts                # 共享接口（RecipeJSON、Tolerance、Profile…）
│       │   ├── constants.ts            # 默认阈值、目标权重、API 路径
│       │   └── index.ts
│       ├── package.json
│       └── tsconfig.json
├── docs/
│   ├── prd.md
│   ├── system_design.md
│   ├── class-diagram.mermaid
│   └── sequence-diagram.mermaid
├── deploy/
│   ├── scf/
│   │   ├── Dockerfile
│   │   └── serverless.yml
│   └── docker-compose.yml              # 本地 pg + redis
├── pnpm-workspace.yaml
├── README.md
└── .gitignore
```

---

## 3. 数据结构和接口（类图 / ER）

### 3.1 后端 ORM 模型（PostgreSQL 核心表 + 关系）

```mermaid
classDiagram
    class User {
        +int id
        +string unionid
        +string openid
        +string nickname
        +datetime created_at
        +datetime updated_at
    }
    class Profile {
        +int id
        +int user_id
        +jsonb target_weights
        +string scale_type
        +datetime created_at
        +datetime updated_at
    }
    class Condition {
        +int id
        +int user_id
        +string name
        +string category
        +jsonb fodmap_flags
        +bool glucose_flag
        +bool histamine_flag
        +bool is_active
        +string note
    }
    class SymptomDef {
        +int id
        +int user_id
        +string name
        +string scale_type
        +int severity_default
        +bool is_custom
    }
    class SymptomLog {
        +int id
        +int user_id
        +int symptom_def_id
        +int meal_log_id
        +int severity
        +datetime logged_at
    }
    class MealLog {
        +int id
        +int user_id
        +datetime eaten_at
        +string note
    }
    class MealItem {
        +int id
        +int meal_log_id
        +int food_id
        +int amount_g
        +string safety_level
    }
    class Challenge {
        +int id
        +int user_id
        +int food_id
        +string status
        +int current_step
        +int target_threshold_g
        +datetime created_at
    }
    class ChallengeStep {
        +int id
        +int challenge_id
        +int step_no
        +int dose_g
        +string status
        +int reaction_severity
        +datetime logged_at
    }
    class Food {
        +int id
        +string name
        +jsonb fodmap_category
        +float gi
        +float gl_per_100g
        +string histamine_level
        +jsonb nutrients
        +jsonb tags
        +string source
    }
    class ToleranceThreshold {
        +int id
        +int user_id
        +int food_id
        +float prior_mean
        +float prior_var
        +float post_mean
        +float post_var
        +int safe_dose_g
        +int caution_dose_g
        +int unsafe_dose_g
        +int n_obs
        +datetime last_updated
    }

    User "1" --> "1" Profile : has
    User "1" --> "*" Condition : records
    User "1" --> "*" SymptomDef : defines
    User "1" --> "*" SymptomLog : logs
    User "1" --> "*" MealLog : eats
    User "1" --> "*" Challenge : challenges
    User "1" --> "*" ToleranceThreshold : tolerates

    MealLog "1" --> "*" MealItem : contains
    MealItem "*" --> "1" Food : references
    SymptomLog "*" --> "1" SymptomDef : of
    SymptomLog "*" --> "1" MealLog : after

    Challenge "1" --> "*" ChallengeStep : steps
    Challenge "*" --> "1" Food : targets

    ToleranceThreshold "*" --> "1" Food : for
```

**字段与关系要点**

- `user`：微信 unionid/openid 唯一；`profile` 为 1:1，存 `target_weights`（JSONB：`{gut:70, glucose:20, fat_loss:10}`）与量表口径。
- `condition`：多状况，每条带 `fodmap_flags`（JSONB，标记冲突维度如 `{"fructan":true,"lactose":true}`）、`glucose_flag`、`histamine_flag`；`is_active` 支持用户覆盖（B6）。
- `symptom_def`：自定义症状词典（A3）；`is_custom` 区分内置/用户定义。
- `symptom_log`：关联 `symptom_def` 与可选 `meal_log`（餐后症状回链）。
- `meal_log` → `meal_item`（1:N）→ `food`（N:1）：餐日志与食物。
- `challenge` → `challenge_step`（1:N）→ `food`：微挑战与剂量步骤。
- `food`：食物库（含 A6 内置预设 + 用户可扩展）；`fodmap_category` JSONB 存六类等级/克，`gl_per_100g` 用于 GL 计算，`nutrients` JSONB。
- `tolerance_threshold`：贝叶斯后验落库（核心表），见 §9.1。

### 3.2 前后端共享类型（`packages/shared`）

```mermaid
classDiagram
    class SafetyLevel {
        <<enum>>
        GREEN = "green"
        YELLOW = "yellow"
        RED = "red"
    }
    class FodmapCategory {
        <<enum>>
        FRUCTAN
        GOS
        LACTOSE
        FRUCTOSE
        SORBITOL
        MANNITOL
    }
    class GoalType {
        <<enum>>
        GUT = "gut"
        GLUCOSE = "glucose"
        FAT_LOSS = "fat_loss"
    }
    class ToleranceDTO {
        +number foodId
        +SafetyLevel safety
        +number safeDoseG
        +number cautionDoseG
        +number unsafeDoseG
        +number nObs
    }
    class RecipeItemDTO {
        +string food
        +number amountG
        +SafetyLevel safety
        +string[] replaceableWith
        +string reason
    }
    class RecipeJSON {
        +string recipeId
        +string title
        +Record~GoalType,number~ targetWeights
        +RecipeItemDTO[] items
        +number totalFodmapLoad
        +number totalGl
        +string burdenWarning
        +string[] steps
        +Nutrition nutrition
        +string[] exploratoryInserts
    }
    class Nutrition {
        +number kcal
        +number proteinG
        +number fatG
        +number carbG
    }
    RecipeJSON "1" *-- "*" RecipeItemDTO : items
    RecipeJSON "1" *-- "1" Nutrition : nutrition
```

`packages/shared/src/enums.ts`、`types.ts`、`constants.ts` 导出上述类型，前端 `services` 直接 import，后端 `schemas` 与之保持字段语义一致（snake_case 在传输层由 Pydantic 别名兼容）。

---

## 4. 程序调用流程（时序图）

### 4.1 ① 注册 / 微信登录

```mermaid
sequenceDiagram
    participant MP as 小程序
    participant Auth as auth.py
    participant WX as wechat.py
    participant DB as User/Profile
    participant Sec as security.py
    MP->>MP: wx.login() 取 code
    MP->>Auth: POST /api/v1/auth/wx-login {code}
    Auth->>WX: code2session(appid, secret, code)
    WX-->>Auth: {openid, unionid}
    Auth->>DB: upsert User(unionid, openid)
    DB-->>Auth: user
    Auth->>DB: ensure Profile(user_id) 默认权重
    Auth->>Sec: create_access_token(user_id)
    Sec-->>Auth: jwt
    Auth-->>MP: {access_token, user}
    MP->>MP: 存 Pinia user store + 本地缓存
```

### 4.2 ② 录入多维画像 + 冲突标注

```mermaid
sequenceDiagram
    participant MP as 小程序
    participant P as profile.py
    participant C as conflict.engine
    participant DB as Condition/SymptomDef
    MP->>P: POST /api/v1/profile/conditions {name, fodmap_flags,...}
    P->>DB: upsert Condition
    P->>C: compute_conflicts(user_id)
    C->>DB: 读所有 active Condition + Food
    C->>C: 交集/并集 + 冲突食物标注
    C-->>P: conflicts[]
    P-->>MP: {conditions, conflicts}
    MP->>MP: 渲染冲突标注区（IBS忌口 vs 血糖友好）
    MP->>P: POST /api/v1/profile/symptoms (自定义症状 A3)
    P->>DB: upsert SymptomDef(is_custom)
    P-->>MP: {symptom_defs}
```

### 4.3 ③ 微挑战 + 餐日志录入 → 贝叶斯更新后验

```mermaid
sequenceDiagram
    participant MP as 小程序
    participant CH as challenge.py
    participant ML as meal/日志
    participant T as tolerance.update
    participant P as prior.py
    participant DB as ToleranceThreshold/MealLog
    MP->>CH: POST /api/v1/challenge {food_id} (为🔴生成计划 B2)
    CH->>P: get_prior(food_id) (A6 知识库)
    P-->>CH: {prior_mean, prior_var}
    CH->>CH: 起点 = safe*0.5 (§6-Q2)
    CH->>DB: 建 Challenge + Steps(50/70/90g)
    CH-->>MP: challenge plan
    MP->>CH: POST /api/v1/challenge/{id}/step 记录反应(severity)
    CH->>T: update(food_id, dose_g, severity)
    T->>DB: 读 ToleranceThreshold(先验/上次后验)
    T->>T: log-normal 共轭更新(§9.1)
    T->>DB: 写 后验 + safe/caution/unsafe_g
    T-->>CH: new_threshold
    CH-->>MP: 步骤完成 + 三色可能变化
    Note over MP,DB: 餐日志同理：POST /api/v1/meal → MealLog/MealItem → 触发 tolerance.update
```

### 4.4 ④ 食谱生成（贝叶斯输出 + 约束 → DeepSeek → 结构化食谱）

```mermaid
sequenceDiagram
    participant MP as 小程序
    participant R as recipe.py
    participant T as tolerance (查询)
    participant C as conflict.engine
    participant B as burden (计算)
    participant D as recipe.client (DeepSeek)
    participant F as recipe.fallback
    MP->>R: POST /api/v1/recipe {target_weights, body_state}
    R->>T: get_thresholds(user_id) → 三色 + 剂量
    R->>C: get_conflicts(user_id)
    R->>B: get_burden_limits(user_id) → FODMAP/GL 阈值
    R->>D: generate(prompt=画像+阈值+权重+约束)
    alt DeepSeek 成功且 JSON 合法
        D-->>R: RecipeJSON
    else 超时/解析失败
        D-->>R: error
        R->>F: template_generate(🟢库70% + 探索插入)
        F-->>R: RecipeJSON(burden_warning="模板生成")
    end
    R->>B: validate(RecipeJSON) → total_fodmap/gl
    R-->>MP: {recipe, burden_warning}
    MP->>MP: 渲染食谱卡 + 一键替换 + 预警
```

### 4.5 ⑤ 组合负担（FODMAP / GL）预警

```mermaid
sequenceDiagram
    participant MP as 小程序
    participant B as burden.fodmap / burden.gl
    participant DB as Food / ToleranceThreshold
    MP->>B: 计算(meal_items[] 或 recipe.items[])
    B->>DB: 取每 food 的 fodmap_category / gl_per_100g
    B->>B: FODMAP六类 Σ + GL Σ
    B->>B: 对比 用户阈值(医学默认/历史微调)
    alt 任一 > 阈值
        B-->>MP: {warning: "午餐 GL 偏高", level: red/yellow}
    else 安全
        B-->>MP: {warning: null}
    end
    MP->>MP: BurdenWarning 组件展示 ⚠️
```

---

## 5. 任务列表（有序、含依赖、按实现阶段）

> 优先级标注：`P0`=MVP 必须有；`P1`=MVP 应有；`P2`=远期/规划。依赖指向前置任务编号。

| 任务 | 名称 | 阶段 | 优先级 | 依赖 | 主要产出（源文件） |
|---|---|---|---|---|---|
| **T0** | 项目脚手架与 Monorepo 初始化 | 0 脚手架 | P0 | — | `pnpm-workspace.yaml`、`README.md`、`.gitignore`、`apps/miniprogram/`（Taro 初始化+Pinia+NutUI）、`apps/api/`（FastAPI 骨架+`main.py`+`requirements.txt`+`pyproject.toml`）、`packages/shared/`、`deploy/docker-compose.yml`、`config/*` |
| **T1** | 后端基础：Auth + DB 模型 + 迁移 | 1 后端基础 | P0 | T0 | `core/config.py`、`core/security.py`、`core/deps.py`、`core/wechat.py`、`db/*`、`models/*`（全部 8 个）、`schemas/auth.py`、`api/v1/auth.py`、`alembic.ini`+`migrations/`、`tests/test_auth.py` |
| **T2** | 贝叶斯内核 + 冲突引擎 + 组合负担 + 三色 | 2 内核 | P0 | T1 | `services/tolerance/{prior,update,model}.py`、`services/conflict/engine.py`、`services/burden/{fodmap,gl}.py`、`schemas/{profile,challenge,map}.py`、`api/v1/{profile,challenge,map}.py`、`models/tolerance.py` 落库、`packages/shared/{enums,types,constants}.ts`、`utils/safety.ts`、`stores/tolerance.ts`、`tests/test_tolerance.py`、`tests/test_burden.py` |
| **T3** | DeepSeek 食谱生成接线 | 3 食谱 | P0 | T2 | `services/recipe/{prompt,client,schema,fallback}.py`、`api/v1/recipe.py`、`schemas/recipe.py`、`stores/recipe.ts`、`services/recipe.ts`、`tests/test_recipe.py` |
| **T4** | 前端页面与状态（5 页 + 组件） | 4 前端 | P0 | T1,T2 | `pages/*`（dashboard/profile/challenge/recipe/map）、`components/*`（SafetyBadge/DoseSlider/RadarChart/WeightSlider/BurdenWarning）、`stores/{user,profile,recipe}.ts`、`services/{http,auth,profile,challenge,recipe,map}.ts`、`utils/format.ts`、`app.config.ts`、`main.ts` |
| **T5** | 前后端联调 + 端到端闭环 + H5 同构 | 5 联调 | P0/P1 | T3,T4 | 联调脚本、CORS/域名校验、`config/prod.ts`、H5 登录兜底（`services/auth.ts`）、微信分享差异、`docs/` 接口契约核对 |
| **T6** | 测试 + 部署 | 6 测试/部署 | P0/P2 | T5 | `tests/*` 补全、CI（`pyproject.toml` pytest）、`deploy/scf/{Dockerfile,serverless.yml}`、本地 `docker-compose` 验证、隐私合规（F3）检查清单 |

**MVP 范围核对**：T0–T5 + T6 的 P0 部分覆盖 PRD §5.1（A1–A4、B1–B5、C1–C7、D1、F1–F3/F5；F4 Redis 为 P1 可后置）。T6 的 P2（Neo4j F6、热力图 D2 等）属远期。

---

## 6. 依赖包列表

### 6.1 前端 `apps/miniprogram/package.json`（关键依赖）

```jsonc
{
  "dependencies": {
    "@tarojs/taro": "^3.6.0",
    "@tarojs/components": "^3.6.0",
    "@tarojs/react": "^3.6.0",
    "@tarojs/plugin-platform-weapp": "^3.6.0",
    "@tarojs/plugin-platform-h5": "^3.6.0",
    "@tarojs/vite-runner": "^3.6.0",
    "vue": "^3.4.0",
    "pinia": "^2.1.0",
    "@nutui/nutui-taro": "^4.2.0",
    "@nutui/icons-vue-taro": "^4.2.0",
    "echarts": "^5.5.0",
    "@wushi/shared": "workspace:*"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "@tarojs/vite-runner": "^3.6.0"
  }
}
```
> 说明：图表在 weapp 端经 `echarts-for-weixin` 轻量引入（`RadarChart.vue` 内条件打包），H5 端直接用 `echarts`；请求层用 `Taro.request` 封装，不引入 axios。

### 6.2 后端 `apps/api/requirements.txt`（关键依赖）

```
fastapi==0.111.*
uvicorn[standard]==0.29.*
sqlalchemy==2.0.*
alembic==1.13.*
pydantic==2.7.*
pydantic-settings==2.2.*
numpyro==0.13.*
jax==0.4.*
jaxlib==0.4.*
scikit-learn==1.4.*            # 仅 A6 知识库辅助（聚类/标准化）
httpx==0.27.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
bcrypt==4.1.*
asyncpg==0.29.*
redis==5.0.*                   # F4 可选
python-multipart==0.0.9
orjson==3.10.*
pytest==8.2.*                  # dev
```

---

## 7. 共享知识（跨文件约定）

### 7.1 命名规范
- 后端：表名 `snake_case` 复数（`meal_log`、`tolerance_threshold`）；字段 `snake_case`；路由函数 `snake_case`；服务类 `CamelCase`。
- 前端：组件 `PascalCase.vue`；store/文件 `camelCase.ts`；变量 `camelCase`；API 传输字段与后端一致（Pydantic `alias` 兼容 snake）。
- 共享枚举/常量集中在 `packages/shared`，禁止在两端各自硬编码安全等级/症状名。

### 7.2 API 路径规范
- 统一前缀 `/api/v1/`；五大域：`auth`、`profile`、`challenge`、`recipe`、`map`。
- 资源风格：`GET /profile/conditions`、`POST /challenge`、`POST /recipe`、`GET /map/radar`。
- 版本演进：v1 锁定（F5），破坏性变更升 v2，不破坏 v1。

### 7.3 统一响应格式与错误码
所有响应包 `{code, message, data}`：
- `code=0` 成功；`data` 业务体。
- `400xx` 参数错误（`4001` 校验失败，`4002` 约束冲突）
- `401xx` 鉴权（`4010` 未登录，`4011` token 过期）
- `403xx` 权限（`4030` 越权访问他人数据）
- `404xx` 资源不存在
- `422xx` 业务规则（`4221` 剂量超限，`4222` 冲突未解决）
- `500xx` 服务错误（`5000` 未知，`5040` 上游 DeepSeek 超时 → 触发回退）
- `5040` 明确触发模板回退并带 `burden_warning`。

### 7.4 环境变量（`core/config.py` 读取）
```
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-pro
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/wushi
REDIS_URL=redis://localhost:6379/0      # 可选
JWT_SECRET=xxx
JWT_ALGORITHM=HS256
WECHAT_APPID=wx...
WECHAT_SECRET=...
CORS_ORIGINS=https://h5.wushi.app
```

### 7.5 数据契约位置
- 所有共享枚举/接口/常量 = `packages/shared/src/{enums,types,constants}.ts`，前端直接 import；后端以同名语义实现 Pydantic schema（字段对齐）。
- 接口契约变更需同步改 `packages/shared` 并通知双方。

### 7.6 状态管理约定（Pinia）
- `user` store：登录态、token、基本信息（唯一写 token 处）。
- `profile` store：状况列表、冲突标注、症状词典（服务端为权威，本地为缓存）。
- `tolerance` store：三色与耐受阈值（镜像后端计算，用于首页即时展示；服务端重算为准）。
- `recipe` store：当前食谱、目标权重（默认来自 `Profile.target_weights`）。
- 规则：stores 不直接写 DB，统一经 `services/*` 调 `/api/v1`；写操作后刷新对应 store。

---

## 8. 待明确事项（PRD §6 逐条建议）

> 标注 **【需用户拍板】** 的必须由主理人/用户确认；其余已给可落地默认方案。

1. **贝叶斯冷启动（无日志初始化）**
   - 建议：用 **A6 内置食物-症状知识库** 作为先验——每食物 `food` 表预置 `fodmap_category/gi/gl/histamine`，`tolerance.prior.py` 据此生成 `prior_mean/prior_var`（如高 FODMAP 食物 prior_mean 低、方差大；低 FODMAP 高）。无任何数据时 `safe_dose_g` 取保守默认（如知识库建议的 50%）。
   - 默认方案：采纳知识库先验 + 保守默认。**【可拍板确认采用 A6 作为默认先验】**（建议同意，非阻断）。

2. **微挑战最低安全剂量起点（无数据食物）**
   - 建议：起点 = `safe_dose_g（先验） * 0.5`（保守半量），后续步骤按 +40% 递增（50→70→98…），收敛后写入后验。无数据食物用知识库保守默认（如 10g 起）。
   - 默认方案：先验半量起，无需拍板。

3. **微信小程序类目资质（健康/医疗边界）【需用户拍板·合规高危】**
   - 建议：定位为 **"食品/健康管理"** 类目，**明确不做诊断、不开方、不宣称疗效**，规避医疗类目资质（需《互联网医疗信息服务资格证》）。隐私政策 + 健康数据加密 + 用户授权弹窗（F3）必做。
   - **【必须用户拍板】**：是否接受"健康管理"定位（不做医疗诊断）？是否需要外包/自办 ICP 备案与类目资质？此点影响上线合规，建议尽早确认。

4. **DeepSeek 接入方式与成本**
   - 建议：单次食谱 `max_tokens` 限制（≤1200）、prompt 前缀缓存、结果按"约束哈希"缓存 24h（Redis）、异步生成（F4）。预算上限建议设月度配额告警。
   - **【需用户拍板】**：月度 token 预算上限？是否允许"超时/失败 → 纯模板生成"作为默认体验（建议允许，保证可用性）。

5. **数据合规：上云 vs 本地优先【需用户拍板】**
   - 建议：默认 **上云（腾讯云）加密存储**（传输 TLS、静态字段级加密敏感健康数据），提供"数据导出/注销删除"按钮（合规刚需）；"本地优先"模式列为 P2（仅本地 + 可选同步）。
   - **【需用户拍板】**：默认上云是否可接受（建议接受，并提供删除权）？涉及《个人信息保护法》告知同意。

6. **多病冲突"求交集"是否允许用户手动覆盖（B6）**
   - 建议：允许覆盖。`condition.is_active` + 用户覆盖记录；冲突引擎默认"求交集"（最严），用户可切"取并集"或单食物豁免，持久化。
   - 默认方案：允许覆盖，无需拍板。

7. **减脂 vs 平稳血糖权重冲突裁决（C1）**
   - 建议：**硬约束优先**——肠道稳定为 P0 硬约束（安全剂量不可破）；血糖/减脂为软加权（归一化求和）。冲突时按权重线性加权生成目标函数，且任何方案不得突破 🔴 阈值。
   - 默认方案：硬约束优先，无需拍板。

8. **小程序 / H5 同构差异（登录与分享）【需用户拍板·影响 T4/T5】**
   - 建议：登录——小程序 `wx.login` code2session；H5 用微信网页授权（需公众号）或手机号+验证码兜底。分享——小程序 `onShareAppMessage`；H5 用 Web Share API。
   - **【需用户拍板】**：H5 是否同期上线（决定登录兜底方案与分享实现工作量）？建议小程序先上线、H5 紧随。

9. **Neo4j 降级 JSON 的迁移路径**
   - 建议：MVP 用 `JSONB`（food 关系、conflict 标注、tolerance 关联）存储；通过 **repository 模式** 隔离存储细节，未来切 Neo4j 只换 repository 后端，模型/服务不变。
   - 默认方案：JSONB + repository 隔离，无需拍板。

10. **组合负担阈值（FODMAP/GL）个性化标定来源**
    - 建议：默认用 **医学建议值**（FODMAP/餐上限、GL/餐上限，如 GL>20 中负荷预警），用户可在 B3 中手动微调；历史数据用于"个性化下调"（可选学习）。
    - 默认方案：医学默认 + 手动可调；**【建议拍板】是否允许系统据历史自动下调阈值**（建议默认关、手动开）。

---

## 9. 重点机制详解（必须讲清的四个点）

### 9.1 贝叶斯个人耐受内核

**机制链路**：冷启动先验（A6 知识库）→ 似然（每次微挑战/餐日志）→ 后验（每食物个性化安全剂量分布）→ 落库 `tolerance_threshold`。

**模型选择：对数正态剂量-阈值模型（log-normal threshold model）**

对食物 `f`、用户 `u`，设真实耐受阈值 `θ_{u,f}`（克，超过则易出现症状）。在 log 空间 `η = log θ ~ N(μ, σ²)`。

- **先验（冷启动）**：来自 A6 知识库 `prior.py`：
  - 高 FODMAP / 高组胺 / 高 GI 食物 → `μ0` 偏低（如 log(20)）、`σ0²` 偏大（不确定性高）。
  - 低 FODMAP / 安全食物 → `μ0` 偏高（如 log(150)）、`σ0²` 偏小。
  - 无任何数据食物 → 保守默认 `μ0=log(50), σ0²=1.0`。

- **似然（区间删失观测）**：每次观测 `i` 含 `(dose_i, severity_i)`：
  - 若 `severity_i == 0`（无症状，安全）→ 证据 `θ > dose_i` → 伪观测 `z_i = log(dose_i) + m`（软下界，`m≈0.3`）。
  - 若 `severity_i > 0`（不耐受）→ 证据 `θ < dose_i` → 伪观测 `z_i = log(dose_i) - m`（软上界）。
  - 严重度可软化边界：`m` 随 `severity/10` 增大（症状越重，阈值越可能远低于 dose）。

- **后验更新（正态共轭，闭式、可在线）**：
  ```
  先验精度  τ0 = 1/σ0²
  对每个伪观测 (z_i, s²)（s² 为大方差，如 1.0）：
      τn = τ0 + Σ 1/s²
      μn = (τ0·μ0 + Σ z_i/s²) / τn
  后验 σn² = 1/τn
  ```
  （MVP 用闭式近似；NumPyro（`model.py`）用于采样验证与未来 SVI 多因素联合推断。）

- **安全剂量分位（落库字段）**：
  ```
  safe_dose_g    = round(exp(μn + z_{0.05}·σn))   # 5% 分位，保守
  caution_dose_g = round(exp(μn))                  # 中位数
  unsafe_dose_g  = round(exp(μn + z_{0.95}·σn))    # 95% 分位
  ```
  `z` 为标准正态分位数（≈±1.645）。

- **落库（`tolerance_threshold` 表字段）**：`prior_mean, prior_var`（log 空间先验）、`post_mean, post_var`（上次后验）、`safe/caution/unsafe_dose_g`、`n_obs`（观测数）、`last_updated`。每次日志/挑战步骤触发 `update.py` 增量更新（读旧后验作新先验，叠加新观测），O(1) 可在线。

- **冷启动质量依赖 A6**：A6 知识库越完整，先验越准，早期三色与微挑战起点越合理。

### 9.2 DeepSeek 食谱生成接线

**Prompt 工程（注入顺序）**
1. `system`：资深营养师 + 食物耐受专家，严格输出 JSON、不诊断、不破安全阈值。
2. `user` 注入：
   - 用户画像（状况 + 冲突标注摘要）
   - 三色等级与耐受阈值（每食物 `safe/caution/unsafe` 克）
   - 目标权重 `{gut:70, glucose:20, fat_loss:10}`
   - 组合负担约束（FODMAP/餐 ≤ X、GL/餐 ≤ Y）
   - 探索性插入要求（1–2 种 🟡 冲突食物按 `safe*0.7` 剂量）
   - 身体状态（如"今日偏腹泻 → 降 FODMAP"）
   - 输出 schema 示例

**食谱 JSON Schema（后端 `recipe/schema.py` 校验，前端 `RecipeJSON` 对齐）**
```json
{
  "recipe_id": "string",
  "title": "string",
  "target_weights": {"gut": 70, "glucose": 20, "fat_loss": 10},
  "items": [
    {
      "food": "鸡胸肉",
      "amount_g": 120,
      "safety": "green",
      "replaceable_with": ["鱼肉", "豆腐"],
      "reason": "低 FODMAP 高蛋白"
    }
  ],
  "total_fodmap_load": 12.5,
  "total_gl": 14.0,
  "burden_warning": null,
  "steps": ["腌制 10 分钟", "中火煎 5 分钟"],
  "nutrition": {"kcal": 420, "protein_g": 38, "fat_g": 14, "carb_g": 30},
  "exploratory_inserts": ["芒果 35g（按安全阈值 70%）"]
}
```

**失败回退策略**
- 触发：`client.py` 超时（>8s）或 `schema.py` 解析/校验失败 → 返回 `5040`。
- 回退 `fallback.py`：从 🟢 安全库抽 70%（C2）+ 按 70% 阈值插入 1–2 种 🟡（C4）→ 组装 `RecipeJSON`，`burden_warning="模板生成（AI 暂不可用）"`。
- 保证：任何情况下用户都能拿到可执行食谱，体验不中断。

**成本控制**
- `max_tokens` ≤ 1200；画像前缀进 prompt 缓存；结果按 `hash(用户约束)` 缓存 24h（Redis，可选）；异步生成（F4）。

### 9.3 组合负担（FODMAP / GL）

- **FODMAP 六类**：Fructan、GOS、Lactose、Fructose、Sorbitol、Mannitol。每食物 `food.fodmap_category` JSONB 存各类型含量（克/100g 或等级）。
  - 单餐总量 = Σ(food.amount_g/100 × 该类型含量)。
  - 预警：任一类型 > 类阈值 **或** 六类总 > 总阈值 → `BurdenWarning`（红/黄）。
- **GL（血糖负荷）**：`GL = Σ(food.amount_g/100 × gl_per_100g)`。
  - 预警：单餐 GL > 用户阈值（医学默认，如 >20 中负荷）→ 预警。
- **个性化**：阈值来源 = 医学建议默认，用户可在 B3 手动微调；可选据历史自动下调（§8-Q10，默认关）。
- **与食谱联动**：`recipe.py` 生成后 `burden.validate` 计算 `total_fodmap_load/total_gl`，超阈值则 `burden_warning` 提示并在前端 `BurdenWarning` 展示。

### 9.4 三色安全等级（🟢/🟡/🔴）

**输入**：①画像冲突标注（`condition.fodmap_flags/glucose_flag/histamine_flag` 与 `food` 的冲突矩阵）②贝叶斯后验（`safe/caution/unsafe_dose_g`）③用户"心爱"标记（`challenge` 关联或手动标 🔴）。

**计算规则（`utils/safety.ts` 与后端一致镜像）**
- **🔴 心爱禁忌**：食物与任一 active 状况**硬冲突**（如高 FODMAP ∩ IBS），且无/低耐受数据；或用户手动标记"舍不得"（进微挑战池）。
- **🟢 超级安全**：后验 `safe_dose_g ≥ 常用份量阈值`（如 ≥ 该食物常见单次用量），且与所有状况无硬冲突。
- **🟡 待探索冲突食物**：数据不足（尚未收敛）、处于微挑战中、或部分维度冲突但未达 🔴。

**公式化**
```
conflict = OR_over_conditions( food 与该 condition 在某维度同时触发 )
has_data = n_obs ≥ 3
if conflict and not has_data:        RED
elif not conflict and safe_dose_g ≥ serving:  GREEN
else:                                 YELLOW
# 用户手动标 🔴 → 强制 RED（进挑战）
```
- 常用份量阈值来自 `food` 表 `serving_g`（A6 预设）。
- 三色统计（首页 🟢12 🟡5 🔴3）由 `tolerance` store 聚合 `SafetyLevel`。

---

## 10. 任务依赖图（Mermaid）

```mermaid
graph TD
    T0[任务0 脚手架 Monorepo]
    T1[任务1 后端 Auth+DB]
    T2[任务2 贝叶斯内核+冲突+负担+三色]
    T3[任务3 DeepSeek 食谱]
    T4[任务4 前端页面与状态]
    T5[任务5 联调+H5同构]
    T6[任务6 测试+部署]

    T0 --> T1
    T0 --> T4
    T1 --> T2
    T2 --> T3
    T3 --> T5
    T4 --> T5
    T5 --> T6
```

---

> 设计原则贯穿：简单可用（闭式共轭避免重 MCMC）、模块化（tolerance/conflict/burden/recipe 服务隔离）、可测（每层独立单测）、双内核缺一不可（贝叶斯给阈值与约束，DeepSeek 给可执行食谱，失败回退保证可用性）。
