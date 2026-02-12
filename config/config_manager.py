"""
统一的配置管理类
支持环境变量覆盖、配置验证、多环境配置
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigError(Exception):
    """配置相关异常"""
    pass


class ConfigManager:
    """统一的配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls, config_path: Optional[str] = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器"""
        if self._initialized:
            return
        
        if config_path is None:
            # 默认配置文件路径
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config.yaml'
            )
        
        self.config_path = config_path
        self._load_config()
        self._validate_config()
        self._initialized = True
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                raise ConfigError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            
            # 应用环境变量覆盖
            self._apply_env_overrides()
            
        except yaml.YAMLError as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"加载配置文件失败: {e}")
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        # 环境变量映射规则：CONFIG_SECTION_KEY -> config.section.key
        env_mappings = {
            'BASE_URL': ('base_url', str),
            'TIMEOUT': ('timeout', int),
            'DB_TYPE': ('database', 'type', str),
            'DB_HOST': ('database', 'host', str),
            'DB_PORT': ('database', 'port', int),
            'DB_USER': ('database', 'user', str),
            'DB_PASSWORD': ('database', 'password', str),
            'DB_NAME': ('database', 'database', str),
            'DINGTALK_WEBHOOK_URL': ('dingtalk', 'webhook_url', str),
            'DINGTALK_SECRET': ('dingtalk', 'secret', str),
            'DINGTALK_AT_MOBILES': ('dingtalk', 'at_mobiles', list),
            'DINGTALK_AT_ALL': ('dingtalk', 'at_all', bool),
            'DINGTALK_FORCE_SEND_IN_LOCAL': ('dingtalk', 'force_send_in_local', bool),
        }
        
        for env_key, config_path in env_mappings.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                # 解析配置路径
                if isinstance(config_path, tuple):
                    type_hint = config_path[-1]
                    keys = config_path[:-1]
                else:
                    type_hint = str
                    keys = (config_path,)
                
                # 类型转换
                try:
                    if type_hint == bool:
                        value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif type_hint == int:
                        value = int(env_value)
                    elif type_hint == list:
                        value = [item.strip() for item in env_value.split(',')]
                    else:
                        value = env_value
                    
                    # 设置配置值
                    self._set_nested_value(keys, value)
                except (ValueError, TypeError) as e:
                    raise ConfigError(f"环境变量 {env_key} 的值 '{env_value}' 无法转换为 {type_hint.__name__}: {e}")
    
    def _set_nested_value(self, keys: tuple, value: Any):
        """设置嵌套配置值"""
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def _validate_config(self):
        """验证配置的完整性和正确性"""
        errors = []
        
        # 验证必填项
        if not self._config.get('base_url'):
            errors.append("base_url 未配置")
        
        # 验证数据库配置（如果使用数据库）
        database = self._config.get('database', {})
        if database:
            required_db_keys = ['host', 'user', 'password', 'database']
            for key in required_db_keys:
                if not database.get(key):
                    errors.append(f"database.{key} 未配置")
        
        # 验证超时配置
        timeout = self._config.get('timeout')
        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
            errors.append("timeout 必须是正整数")
        
        if errors:
            raise ConfigError(f"配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套路径）
        
        Args:
            key_path: 配置路径，如 'database.host' 或 'base_url'
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_base_url(self) -> str:
        """获取基础URL"""
        return self.get('base_url', '')
    
    def get_timeout(self) -> int:
        """获取超时时间"""
        return self.get('timeout', 30)
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get('database', {})
    
    def get_token_config(self) -> Dict[str, Any]:
        """获取Token配置"""
        return self.get('token', {})

    def get_default_headers(self) -> Dict[str, Any]:
        """获取全局默认请求头配置"""
        headers = self.get('headers', {}) or {}
        return headers if isinstance(headers, dict) else {}
    
    def get_dingtalk_config(self) -> Dict[str, Any]:
        """获取钉钉配置"""
        return self.get('dingtalk', {})
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return self.get('redis', {})
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
        self._validate_config()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    获取配置管理器实例（单例）
    
    Args:
        config_path: 配置文件路径（可选）
    
    Returns:
        ConfigManager实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager
