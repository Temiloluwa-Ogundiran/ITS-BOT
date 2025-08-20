"""
Configuration management for the Helpdesk Knowledge Base system.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class ElasticsearchConfig:
    """Elasticsearch connection configuration."""
    host: str = "localhost"
    port: int = 9200
    use_ssl: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3


@dataclass
class IndexConfig:
    """Elasticsearch index configuration."""
    name: str = "helpdesk_kb"
    number_of_shards: int = 1
    number_of_replicas: int = 0
    refresh_interval: str = "1s"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None


class ConfigManager:
    """Configuration management for the helpdesk system."""
    
    def __init__(self, environment: Optional[Environment] = None):
        self.environment = environment or Environment(os.getenv('ENVIRONMENT', 'development'))
        
        # Initialize configurations
        self.elasticsearch = ElasticsearchConfig()
        self.index = IndexConfig()
        self.logging = LoggingConfig()
        
        # Load configuration
        self._load_from_env()
        self._apply_environment_overrides()
        
        logging.info(f"Configuration loaded for environment: {self.environment.value}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Elasticsearch settings
        self.elasticsearch.host = os.getenv('ES_HOST', self.elasticsearch.host)
        self.elasticsearch.port = int(os.getenv('ES_PORT', str(self.elasticsearch.port)))
        self.elasticsearch.use_ssl = os.getenv('ES_USE_SSL', 'false').lower() == 'true'
        self.elasticsearch.username = os.getenv('ES_USERNAME')
        self.elasticsearch.password = os.getenv('ES_PASSWORD')
        
        # Index settings
        self.index.name = os.getenv('ES_INDEX_NAME', self.index.name)
        
        # Logging settings
        log_level = os.getenv('LOG_LEVEL', self.logging.level.value)
        try:
            self.logging.level = LogLevel(log_level.upper())
        except ValueError:
            logging.warning(f"Invalid log level: {log_level}, using default")
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides."""
        if self.environment == Environment.DEVELOPMENT:
            self.logging.level = LogLevel.DEBUG
            
        elif self.environment == Environment.PRODUCTION:
            self.logging.level = LogLevel.WARNING
            self.index.number_of_shards = 3
            self.index.number_of_replicas = 2
            self.elasticsearch.timeout = 120
            self.elasticsearch.max_retries = 10
    
    def get_elasticsearch_config(self) -> Dict[str, Any]:
        """Get Elasticsearch configuration as dictionary."""
        config = {
            'hosts': [{'host': self.elasticsearch.host, 'port': self.elasticsearch.port}],
            'use_ssl': self.elasticsearch.use_ssl,
            'timeout': self.elasticsearch.timeout,
            'max_retries': self.elasticsearch.max_retries
        }
        
        if self.elasticsearch.username and self.elasticsearch.password:
            config['http_auth'] = (self.elasticsearch.username, self.elasticsearch.password)
        
        return config
    
    def get_index_config(self) -> Dict[str, Any]:
        """Get index configuration as dictionary."""
        return {
            'name': self.index.name,
            'number_of_shards': self.index.number_of_shards,
            'number_of_replicas': self.index.number_of_replicas,
            'refresh_interval': self.index.refresh_interval
        }


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_elasticsearch_config() -> Dict[str, Any]:
    """Get Elasticsearch configuration."""
    return get_config_manager().get_elasticsearch_config()


def get_index_config() -> Dict[str, Any]:
    """Get index configuration."""
    return get_config_manager().get_index_config()
