from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Helius
    HELIUS_API_KEY: str = ""
    HELIUS_RPC_URL: str = "https://mainnet.helius-rpc.com"

    # App
    APP_NAME: str = "Solarized"
    DEBUG: bool = False

    # Rate limiting
    MAX_TRANSACTIONS_PER_QUERY: int = 1000
    MAX_DEPTH: int = 3  # Niveles de recursión en el grafo

    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hora

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
print(f"🔑 Loaded HELIUS_API_KEY: {settings.HELIUS_API_KEY[:4]}...{settings.HELIUS_API_KEY[-4:] if settings.HELIUS_API_KEY else 'EMPTY'}")
