"""
数据库操作处理器
支持前置SQL和后置SQL操作
支持MySQL和PostgreSQL
"""
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
        self.db_type = None  # 'mysql' 或 'postgresql'
        
        # 使用统一的配置管理器
        try:
            self.config_manager = get_config(config_path)
            self.config = self.config_manager.get_database_config()
        except Exception as e:
            raise DatabaseError(f"加载数据库配置失败: {e}")
    
    def connect(self):
        """建立数据库连接（延迟连接，只在需要时连接）"""
        if self.connection is None:
            try:
                db_type = self.config.get('type', 'postgresql').lower()
                
                if db_type == 'postgresql' or db_type == 'postgres':
                    # PostgreSQL连接
                    import psycopg2
                    from psycopg2.extras import RealDictCursor
                    
                    host = self.config.get('host', 'localhost')
                    port = self.config.get('port', 5432)
                    user = self.config.get('user', 'postgres')
                    password = self.config.get('password', '')
                    database = self.config.get('database', '')
                    
                    try:
                        self.connection = psycopg2.connect(
                            host=host,
                            port=port,
                            user=user,
                            password=password,
                            database=database,
                            cursor_factory=RealDictCursor
                        )
                        self.db_type = 'postgresql'
                    except psycopg2.OperationalError as e:
                        # 提供更详细的错误信息
                        error_msg = str(e)
                        if "Database does not exist" in error_msg:
                            raise Exception(
                                f"数据库连接失败: 数据库 '{database}' 不存在\n"
                                f"连接信息: {user}@{host}:{port}\n"
                                f"请检查配置中的 database 字段是否正确"
                            )
                        else:
                            raise Exception(f"数据库连接失败: {error_msg}")
                else:
                    # MySQL连接（默认）
                    import pymysql
                    
                    self.connection = pymysql.connect(
                        host=self.config.get('host', 'localhost'),
                        port=self.config.get('port', 3306),
                        user=self.config.get('user', 'root'),
                        password=self.config.get('password', ''),
                        database=self.config.get('database', ''),
                        charset=self.config.get('charset', 'utf8mb4'),
                        cursorclass=pymysql.cursors.DictCursor,
                        autocommit=False
                    )
                    self.db_type = 'mysql'
            except ImportError as e:
                db_type = self.config.get('type', 'postgresql').lower()
                if db_type in ['postgresql', 'postgres']:
                    raise Exception(f"PostgreSQL驱动未安装，请运行: pip install psycopg2-binary")
                else:
                    raise Exception(f"MySQL驱动未安装，请运行: pip install pymysql")
            except Exception as e:
                raise Exception(f"数据库连接失败: {str(e)}")
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_sql(self, sql: str, fetch_one: bool = False) -> Optional[Any]:
        """
        执行SQL语句（优化：延迟连接，减少连接检查）
        
        Args:
            sql: SQL语句
            fetch_one: 是否只获取一条记录
        
        Returns:
            查询结果
        """
        # 延迟连接：只在第一次执行SQL时连接
        if self.connection is None:
            self.connect()
        # 检查连接是否仍然有效
        elif not self._is_connection_alive():
            self.disconnect()
            self.connect()
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                
                # 判断SQL类型（优化：使用upper()一次，避免重复调用）
                sql_upper = sql.strip().upper()
                if sql_upper.startswith('SELECT'):
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
            if self.connection:
                self.connection.rollback()
                raise Exception(f"SQL执行失败: {str(e)}")
    def _is_connection_alive(self) -> bool:
        """
        检查数据库连接是否仍然有效
        
        Returns:
            bool: 连接有效返回True，否则返回False
        """
        if self.connection is None:
            return False
        try:
            if self.db_type == 'postgresql':
                # PostgreSQL使用简单的查询来检查连接
                with self.connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
            else:
                # MySQL使用ping方法
                self.connection.ping(reconnect=False)
            return True
        except:
            return False
    
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

