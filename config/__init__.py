"""
配置模块
"""
from .config_manager import ConfigManager, ConfigError, get_config

__all__ = ['ConfigManager', 'ConfigError', 'get_config']
