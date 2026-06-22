"""
Centralized configuration management using pydantic-settings.
All environment variables are loaded here and ONLY here.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Redis Configuration
    num_redis_nodes: int = 3
    max_redis_nodes: int = 5
    redis_cache_ttl: int = 300
    cache_prefix_max_len: int = 20
    virtual_nodes_per_ring: int = 150
    
    # Redis Connection
    redis_node_1_host: str = "redis-node-1"
    redis_node_1_port: int = 6379
    redis_node_2_host: str = "redis-node-2"
    redis_node_2_port: int = 6380
    redis_node_3_host: str = "redis-node-3"
    redis_node_3_port: int = 6381
    redis_node_4_host: str = "redis-node-4"
    redis_node_4_port: int = 6382
    redis_node_5_host: str = "redis-node-5"
    redis_node_5_port: int = 6383
    redis_queue_host: str = "redis-queue"
    redis_queue_port: int = 6384
    
    # Batch Write Configuration
    batch_flush_interval: int = 10
    batch_flush_threshold: int = 100
    batch_max_retries: int = 3
    
    # Trending Configuration
    trending_window_hours: int = 24
    recency_weight: float = 0.3
    
    # Database Configuration
    postgres_user: str = "typeahead_user"
    postgres_password: str = "typeahead_pass"
    postgres_db: str = "typeahead"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    
    # Application
    backend_port: int = 8000
    frontend_port: int = 5173
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def postgres_dsn(self) -> str:
        """Construct PostgreSQL connection string."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    def get_redis_node_config(self, node_num: int) -> dict:
        """Get host and port for a specific Redis node."""
        host_attr = f"redis_node_{node_num}_host"
        port_attr = f"redis_node_{node_num}_port"
        return {
            "host": getattr(self, host_attr),
            "port": getattr(self, port_attr)
        }
    
    def validate_redis_nodes(self) -> None:
        """Validate Redis node configuration at startup."""
        if self.num_redis_nodes > self.max_redis_nodes:
            raise ValueError(
                f"NUM_REDIS_NODES ({self.num_redis_nodes}) cannot exceed "
                f"MAX_REDIS_NODES ({self.max_redis_nodes}). "
                f"Docker Compose only defines {self.max_redis_nodes} Redis cache services."
            )
        if self.num_redis_nodes < 1:
            raise ValueError("NUM_REDIS_NODES must be at least 1")


# Single settings instance - import this everywhere
settings = Settings()
