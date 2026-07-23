"""FastAPI 应用入口。

创建应用实例、配置 CORS、挂载 v1 路由（/api/v1 前缀）、提供健康检查端点。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, profile
from app.core.config import settings

# 创建应用
app = FastAPI(
    title="吾食 Wushi API",
    description="个人食物耐受边界学习系统后端（FastAPI + SQLAlchemy 2.0 async）",
    version="1.0.0",
)

# CORS：生产请明确来源，避免使用 "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 v1 路由（auth -> /api/v1/auth，profile -> /api/v1/profile）
app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")


@app.get("/health", tags=["system"], summary="健康检查")
async def health() -> dict[str, str]:
    """服务健康检查，返回 ``{"status": "ok"}``。"""
    return {"status": "ok"}


@app.get("/", tags=["system"], summary="根路径")
async def root() -> dict[str, str]:
    """根路径欢迎信息。"""
    return {"service": "wushi-api", "docs": "/docs"}
