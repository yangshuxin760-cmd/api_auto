"""
Redis操作处理器
支持从Redis获取验证码等数据
"""
import redis
from typing import Optional, Any
import json


class RedisHandler:
    """Redis处理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化Redis连接
        
        Args:
            config_path: 配置文件路径
        """
        from config.config_manager import get_config
        from utils.exceptions import DatabaseError
        
        self.connection = None
        
        # 使用统一的配置管理器
        try:
            self.config_manager = get_config(config_path)
            self.config = self.config_manager.get_redis_config()
        except Exception as e:
            raise DatabaseError(f"加载Redis配置失败: {e}")
    
    def connect(self):
        """建立Redis连接（延迟连接，只在需要时连接）"""
        if self.connection is None:
            try:
                connection_kwargs = {
                    'host': self.config.get('host', 'localhost'),
                    'port': self.config.get('port', 6379),
                    'db': self.config.get('db', 0),
                }
                # 如果有密码，添加密码参数
                password = self.config.get('password')
                if password and password != 'null' and password != 'None':
                    connection_kwargs['password'] = password
                
                # 尝试使用decode_responses（redis>=3.0支持）
                try:
                    connection_kwargs['decode_responses'] = True
                    self.connection = redis.Redis(**connection_kwargs)
                except TypeError:
                    # 如果不支持decode_responses，使用旧方式
                    self.connection = redis.Redis(**{k: v for k, v in connection_kwargs.items() if k != 'decode_responses'})
                
                # 测试连接
                self.connection.ping()
            except Exception as e:
                raise Exception(f"Redis连接失败: {str(e)}")
    
    def disconnect(self):
        """关闭Redis连接"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
    
    def get(self, key: str) -> Optional[str]:
        """
        获取Redis中的值
        
        Args:
            key: Redis键名
            
        Returns:
            值（字符串），如果不存在返回None
        """
        if self.connection is None:
            self.connect()
        
        try:
            value = self.connection.get(key)
            # 如果返回的是bytes，解码为字符串
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            return value
        except Exception as e:
            raise Exception(f"Redis获取失败: {str(e)}")
    
    def get_verification_code(self, phone: str, key_pattern: str = None) -> Optional[str]:
        """
        获取手机验证码
        
        Args:
            phone: 手机号
            key_pattern: Redis键名模式，支持占位符 {phone}
                        例如: "sms:code:{phone}" 或 "verification:{phone}"
                        如果不提供，使用默认模式: "sms:code:{phone}"
        
        Returns:
            验证码（字符串），如果不存在返回None
        """
        if key_pattern is None:
            key_pattern = self.config.get('code_key_pattern', 'sms:code:{phone}')
        
        # 替换占位符
        key = key_pattern.format(phone=phone)
        
        return self.get(key)
    
    def execute_redis_command(self, command: str, *args) -> Any:
        """
        执行Redis命令
        
        Args:
            command: Redis命令，如 'get', 'hget', 'keys' 等
            *args: 命令参数
        
        Returns:
            命令执行结果
        """
        if self.connection is None:
            self.connect()
        
        try:
            if not hasattr(self.connection, command):
                raise Exception(f"不支持的Redis命令: {command}")
            
            method = getattr(self.connection, command)
            result = method(*args)
            return result
        except Exception as e:
            raise Exception(f"Redis命令执行失败: {str(e)}")
