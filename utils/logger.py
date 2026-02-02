"""
优化的日志系统
支持结构化日志、日志级别配置、文件输出、日志轮转
"""
import os
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（JSON格式）"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON格式"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def formatException(self, exc_info):
        """格式化异常信息"""
        import traceback
        return traceback.format_exception(*exc_info)


class LoggerManager:
    """日志管理器"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls, log_level: str = 'INFO', log_dir: str = 'logs',
                   enable_file: bool = True, enable_console: bool = True,
                   enable_json: bool = False, max_bytes: int = 10 * 1024 * 1024,
                   backup_count: int = 5):
        """
        初始化日志系统
        
        Args:
            log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
            log_dir: 日志文件目录
            enable_file: 是否启用文件日志
            enable_console: 是否启用控制台日志
            enable_json: 是否使用JSON格式（结构化日志）
            max_bytes: 单个日志文件最大字节数
            backup_count: 保留的日志文件数量
        """
        if cls._initialized:
            return
        
        # 创建日志目录
        if enable_file:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 创建格式化器
        if enable_json:
            formatter = StructuredFormatter()
            console_formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # 控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # 文件处理器（所有级别）
        if enable_file:
            all_log_file = os.path.join(log_dir, 'all.log')
            file_handler = RotatingFileHandler(
                all_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # 错误日志文件（只记录ERROR及以上级别）
            error_log_file = os.path.join(log_dir, 'error.log')
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
        
        Returns:
            Logger实例
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        logging.getLogger().setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器（便捷函数）
    
    Args:
        name: 日志记录器名称
    
    Returns:
        Logger实例
    """
    return LoggerManager.get_logger(name)


# 默认初始化日志系统
def init_logger_from_config(config_manager=None):
    """
    从配置初始化日志系统
    
    Args:
        config_manager: 配置管理器实例
    """
    if config_manager is None:
        from config.config_manager import get_config
        config_manager = get_config()
    
    log_config = config_manager.get('logging', {})
    
    LoggerManager.initialize(
        log_level=log_config.get('level', 'INFO'),
        log_dir=log_config.get('dir', 'logs'),
        enable_file=log_config.get('enable_file', True),
        enable_console=log_config.get('enable_console', True),
        enable_json=log_config.get('enable_json', False),
        max_bytes=log_config.get('max_bytes', 10 * 1024 * 1024),
        backup_count=log_config.get('backup_count', 5)
    )
