"""
Configuration file for the Helpdesk Knowledge Base Elasticsearch system.
Contains settings for different environments and connection parameters.
"""

import os
from typing import Dict, Any

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Base configuration
BASE_CONFIG = {
    'index_name': 'helpdesk_kb',
    'number_of_shards': 1,
    'number_of_replicas': 0,
    'refresh_interval': '1s',
    'max_result_window': 10000
}

# Environment-specific configurations
ENVIRONMENTS = {
    'development': {
        'elasticsearch': {
            'host': 'localhost',
            'port': 9200,
            'use_ssl': False,
            'username': None,
            'password': None,
            'timeout': 30,
            'max_retries': 3,
            'retry_on_timeout': True
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'index': {
            **BASE_CONFIG,
            'number_of_replicas': 0
        }
    },
    
    'staging': {
        'elasticsearch': {
            'host': os.getenv('ES_HOST', 'localhost'),
            'port': int(os.getenv('ES_PORT', 9200)),
            'use_ssl': os.getenv('ES_USE_SSL', 'false').lower() == 'true',
            'username': os.getenv('ES_USERNAME'),
            'password': os.getenv('ES_PASSWORD'),
            'timeout': 60,
            'max_retries': 5,
            'retry_on_timeout': True
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'index': {
            **BASE_CONFIG,
            'number_of_replicas': 1
        }
    },
    
    'production': {
        'elasticsearch': {
            'host': os.getenv('ES_HOST', 'localhost'),
            'port': int(os.getenv('ES_PORT', 9200)),
            'use_ssl': os.getenv('ES_USE_SSL', 'true').lower() == 'true',
            'username': os.getenv('ES_USERNAME'),
            'password': os.getenv('ES_PASSWORD'),
            'timeout': 120,
            'max_retries': 10,
            'retry_on_timeout': True,
            'sniff_on_start': True,
            'sniff_on_connection_fail': True,
            'sniffer_timeout': 60
        },
        'logging': {
            'level': 'WARNING',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'index': {
            **BASE_CONFIG,
            'number_of_shards': 3,
            'number_of_replicas': 2
        }
    }
}

# Get current environment configuration
def get_config() -> Dict[str, Any]:
    """Get configuration for the current environment."""
    return ENVIRONMENTS.get(ENVIRONMENT, ENVIRONMENTS['development'])

def get_elasticsearch_config() -> Dict[str, Any]:
    """Get Elasticsearch configuration for the current environment."""
    return get_config()['elasticsearch']

def get_index_config() -> Dict[str, Any]:
    """Get index configuration for the current environment."""
    return get_config()['index']

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration for the current environment."""
    return get_config()['logging']

# Elasticsearch connection settings
ELASTICSEARCH_CONFIG = get_elasticsearch_config()

# Index settings
INDEX_CONFIG = get_index_config()

# Logging settings
LOGGING_CONFIG = get_logging_config()

# Search settings
SEARCH_CONFIG = {
    'default_size': 10,
    'max_size': 100,
    'default_timeout': '30s',
    'highlight_fields': ['title', 'content', 'symptoms', 'keywords'],
    'suggest_fields': ['title', 'content'],
    'fuzzy_settings': {
        'fuzziness': 'AUTO',
        'prefix_length': 2,
        'max_expansions': 50
    }
}

# Analyzer settings
ANALYZER_CONFIG = {
    'content_analyzer': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['lowercase', 'stop', 'snowball', 'word_delimiter_graph'],
        'stopwords': '_english_'
    },
    'symptom_analyzer': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['lowercase', 'stop', 'snowball', 'word_delimiter_graph', 'synonym_filter'],
        'stopwords': '_english_'
    },
    'keyword_analyzer': {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': ['lowercase', 'word_delimiter_graph', 'unique']
    }
}

# Synonym mappings
SYNONYM_MAPPINGS = [
    "email, mail, e-mail, electronic mail",
    "password, pwd, pass, passwd",
    "username, user, login, userid",
    "computer, pc, desktop, laptop",
    "internet, web, online, network",
    "printer, print, printing",
    "software, program, application, app",
    "hardware, device, equipment",
    "error, issue, problem, bug, fault",
    "solution, fix, resolve, repair",
    "restart, reboot, reset",
    "update, upgrade, patch",
    "install, setup, configure",
    "uninstall, remove, delete",
    "screen, monitor, display",
    "keyboard, keys, typing",
    "mouse, pointing device, cursor",
    "file, document, data",
    "folder, directory, location",
    "network, wifi, wireless, ethernet"
]

# Validation rules
VALIDATION_RULES = {
    'required_fields': ['title', 'content', 'category', 'difficulty_level'],
    'difficulty_levels': ['easy', 'medium', 'hard'],
    'max_title_length': 200,
    'max_content_length': 10000,
    'max_keywords': 20,
    'max_symptoms': 15,
    'max_solution_steps': 20,
    'max_diagnostic_questions': 10,
    'success_rate_range': (0.0, 1.0),
    'estimated_time_range': (1, 480)  # 1 minute to 8 hours
}

# Performance settings
PERFORMANCE_CONFIG = {
    'bulk_size': 1000,
    'bulk_timeout': '60s',
    'search_timeout': '30s',
    'index_refresh_interval': '1s',
    'max_result_window': 10000
}

# Security settings
SECURITY_CONFIG = {
    'enable_ssl_verification': True,
    'enable_authentication': False,
    'allowed_hosts': ['localhost', '127.0.0.1'],
    'max_connections': 100,
    'connection_timeout': 30
}

if __name__ == "__main__":
    # Print current configuration
    print(f"Current Environment: {ENVIRONMENT}")
    print(f"Elasticsearch Config: {ELASTICSEARCH_CONFIG}")
    print(f"Index Config: {INDEX_CONFIG}")
    print(f"Logging Config: {LOGGING_CONFIG}")
