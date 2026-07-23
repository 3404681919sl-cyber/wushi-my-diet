"""应用配置（pydantic-settings）。

从环境变量 / ``.env`` 读取配置。所有 Settings 字段均需在 ``.env.example`` 中提供说明，
保证配置齐全、可移植。

生产目标数据库为 ``postgresql+asyncpg://...``；本地无 PostgreSQL 时可临时使用
``sqlite+aiosqlite:///./dev.db`` 验证（JSONB 字段在 SQLite 下自动编译为 JSON）。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- 数据库 ----------
    DATABASE_URL: str = "postgresql+asyncpg://wushi:wushi@localhost:5432/wushi"

    # ---------- Redis（可选，F4，本期未强制）----------
    REDIS_URL: str | None = None

    # ---------- JWT ----------
    JWT_SECRET: str = "change-me-in-production-please-replace"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 默认 7 天

    # ---------- DeepSeek（T3 食谱生成，本期预留）----------
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"

    # ---------- 微信开放平台（T1 预留 wechat-login）----------
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    # ---------- CORS ----------
    # 支持逗号分隔的字符串或列表；生产请明确来源，避免使用 "*"
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def cors_origins_list(self) -> list[str]:
        """返回 CORS 允许来源列表（兼容字符串与列表两种配置形态）。"""
        if isinstance(self.CORS_ORIGINS, str):
            return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]
        return list(self.CORS_ORIGINS)


@lru_cache
def get_settings() -> Settings:
    """返回进程级单例配置（带缓存）。"""
    return Settings()


# 全局配置实例（导入即生效）
settings: Settings = get_settings()
