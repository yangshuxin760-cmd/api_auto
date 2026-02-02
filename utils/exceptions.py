"""
自定义异常类
提供更详细的错误信息和错误分类
"""
from typing import Optional, Dict, Any


class TestFrameworkError(Exception):
    """测试框架基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化异常
        
        Args:
            message: 错误消息
            details: 错误详情（字典格式）
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """返回格式化的错误信息"""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class ConfigError(TestFrameworkError):
    """配置相关异常"""
    pass


class TestCaseError(TestFrameworkError):
    """测试用例相关异常"""
    pass


class ValidationError(TestCaseError):
    """用例格式验证异常"""
    pass


class AssertionError(TestCaseError):
    """断言失败异常"""
    
    def __init__(self, message: str, expected: Any = None, actual: Any = None, 
                 field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        初始化断言失败异常
        
        Args:
            message: 错误消息
            expected: 期望值
            actual: 实际值
            field: 字段名
            details: 其他详情
        """
        details = details or {}
        if expected is not None:
            details['expected'] = expected
        if actual is not None:
            details['actual'] = actual
        if field:
            details['field'] = field
        
        super().__init__(message, details)
        self.expected = expected
        self.actual = actual
        self.field = field


class RequestError(TestFrameworkError):
    """HTTP请求相关异常"""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None, response: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化请求异常
        
        Args:
            message: 错误消息
            url: 请求URL
            status_code: HTTP状态码
            response: 响应内容
            details: 其他详情
        """
        details = details or {}
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        if response:
            details['response'] = response
        
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code
        self.response = response


class DatabaseError(TestFrameworkError):
    """数据库操作相关异常"""
    
    def __init__(self, message: str, sql: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化数据库异常
        
        Args:
            message: 错误消息
            sql: SQL语句
            details: 其他详情
        """
        details = details or {}
        if sql:
            details['sql'] = sql
        
        super().__init__(message, details)
        self.sql = sql


class PreLoginError(TestFrameworkError):
    """前置登录相关异常"""
    pass
