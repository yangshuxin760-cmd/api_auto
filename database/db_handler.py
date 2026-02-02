"""
数据库操作处理器
支持前置SQL和后置SQL操作
"""
import pymysql
from typing import Dict, Any, List, Optional
import yaml
import os


class DatabaseHandler:
    """数据库处理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化数据库连接
        
        Args:
            config_path: 配置文件路径（已废弃，保留以兼容旧代码）
        """
        from config.config_manager import get_config
        from utils.exceptions import DatabaseError
        
        self.connection = None
        
        # 使用统一的配置管理器
        try:
            self.config_manager = get_config(config_path)
            self.config = self.config_manager.get_database_config()
        except Exception as e:
            raise DatabaseError(f"加载数据库配置失败: {e}")
    
    def connect(self):
        """建立数据库连接"""
        if self.connection is None:
            self.connection = pymysql.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 3306),
                user=self.config.get('user', 'root'),
                password=self.config.get('password', ''),
                database=self.config.get('database', ''),
                charset=self.config.get('charset', 'utf8mb4'),
                cursorclass=pymysql.cursors.DictCursor
            )
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_sql(self, sql: str, fetch_one: bool = False) -> Optional[Any]:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            fetch_one: 是否只获取一条记录
        
        Returns:
            查询结果
        """
        if self.connection is None:
            self.connect()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                
                # 判断SQL类型
                if sql.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                else:
                    # INSERT, UPDATE, DELETE等操作
                    self.connection.commit()
                    result = cursor.rowcount
                
                return result
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"SQL执行失败: {str(e)}")
    
    def execute_pre_sql(self, sql: str) -> Optional[Any]:
        """
        执行前置SQL
        
        Args:
            sql: SQL语句
        
        Returns:
            查询结果，可用于后续接口参数
        """
        return self.execute_sql(sql, fetch_one=True)
    
    def execute_post_sql(self, sql: str):
        """
        执行后置SQL
        
        Args:
            sql: SQL语句
        """
        self.execute_sql(sql)

