"""应用统一配置。

所有配置项通过环境变量注入，禁止在代码中硬编码密钥。
本地开发时读取 backend/.env 文件。
"""

from functools import lru_cache
from typing import Any, List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置对象。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 运行环境 ----------
    APP_ENV: str = "local"

    # ---------- 服务基础 ----------
    APP_NAME: str = "生活助手后端"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ---------- 数据库 ----------
    DATABASE_URL: str = "sqlite:///./life_assistant.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # ---------- 鉴权 ----------
    JWT_SECRET_KEY: str = "dev-only-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 7200
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # ---------- 业务时区 ----------
    BUSINESS_TIMEZONE: str = "Asia/Shanghai"

    # ---------- 跨域 ----------
    # 用 Union[str, List[str)] 声明，避免 pydantic-settings 在读取 .env 时
    # 强制把该字段当成 JSON 解析（支持 CORS_ORIGINS=a,b,c 逗号分隔写法）。
    CORS_ORIGINS: Union[str, List[str]] = "*"

    # ---------- 第三方 ----------
    WEATHER_PROVIDER: str = ""
    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE_URL: str = ""
    WEATHER_TIMEOUT_SECONDS: int = 5
    WEATHER_CACHE_MINUTES: int = 30

    # ---------- 日志 ----------
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def _split_cors(cls, v: Any) -> List[str]:
        """支持 CORS_ORIGINS=a,b,c 逗号分隔写法。"""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [item.strip() for item in v.split(",") if item.strip()]
        return list(v)

    @property
    def cors_origins_list(self) -> List[str]:
        """统一取跨域白名单列表。"""
        return self._split_cors(self.CORS_ORIGINS)

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "prod"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取配置单例。"""
    return Settings()


settings = get_settings()
