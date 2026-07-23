# 吾食（Wushi）后端 —— 腾讯云 SCF 容器镜像 Web 函数构建镜像
# 基础镜像：Debian 系 slim，含 pip 与基础编译工具链。
FROM python:3.11-slim

# ---- 1. 系统构建依赖 ----
# 编译 asyncpg / cryptography / bcrypt 等需要 gcc，先装好再装 Python 包。
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# ---- 2. 安装 Python 依赖 ----
WORKDIR /app

# 先升级 pip，再按依赖清单安装运行时依赖。
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 说明：requirements.txt 未包含 gunicorn，但生产容器用 gunicorn + UvicornWorker
# 托管 ASGI 更稳定，故在此一并安装。若后续把 gunicorn 写入 requirements.txt，
# 可删除下面这一行。
RUN pip install --no-cache-dir gunicorn

# ---- 3. 复制应用代码 ----
# 复制顺序：依赖清单在前（已利用缓存），代码在后，便于镜像层缓存。
COPY . .

# ---- 4. 端口 ----
EXPOSE 8000

# ---- 5. 启动：优先 gunicorn（已在上方内置安装）----
# 所有配置均从环境变量读取（DATABASE_URL / DEEPSEEK_API_KEY / JWT_SECRET / CORS_ORIGINS），
# 密钥绝不写死进镜像，由 SCF 环境变量 / 密钥管理在运行时注入。
# 腾讯云 SCF 容器镜像 Web 函数默认注入 PORT=9000，平台把流量转发到该端口；
# 这里读取 ${PORT:-8000}：部署到 SCF 时自动监听 9000，平台流量可达；
# 本地直接 `docker run -p 8000:8000 ...` 调试时 PORT 未设置，回退到 8000。
# 注意：用 shell 形式（非 exec 数组）以便 ${PORT:-8000} 由 /bin/sh 展开。
CMD gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} -w 2
