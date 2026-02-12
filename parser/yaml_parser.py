"""
YAML测试用例解析器
支持中文关键字驱动的YAML格式解析
"""
import yaml
import os
from typing import Dict, Any, List


class YamlParser:
    """YAML测试用例解析器 - 支持中文关键字驱动"""
    
    # 中文关键字到英文关键字的映射
    KEYWORD_MAPPING = {
        # 用例基本信息
        '用例名称': 'name',
        '用例描述': 'description',
        '用例列表': 'test_cases',
        # 控制开关
        '不使用token': 'no_token',
        # 请求相关
        '请求方法': 'method',
        '请求地址': 'url',
        '请求头': 'headers',
        '请求参数': 'params',
        '请求体': 'json',
        '表单数据': 'data',
        # SQL相关
        '前置SQL': 'pre_sql',
        '后置SQL': 'post_sql',
        # Redis相关
        '前置Redis': 'pre_redis',
        'Redis配置': 'pre_redis',
        'Redis键模式': 'redis_key_pattern',
        # 登录相关
        '前置登录': 'pre_login',
        '自动注册': 'auto_register',
        '登录接口': 'login_url',
        '登录方法': 'login_method',
        '登录请求体': 'login_body',
        '注册接口': 'register_url',
        '用户名': 'username',
        '密码': 'password',
        # 断言相关
        '断言': 'assertions',
        '状态码': 'status_code',
        '字段断言': 'fields',
        '字段': 'field',
        '不为空': 'not_empty',
        '期望值': 'expected_value',
        '响应不为空': 'not_empty',  # 在断言下的响应不为空
    }
    
    def __init__(self, yaml_file: str):
        """
        初始化解析器
        
        Args:
            yaml_file: YAML测试用例文件路径
        """
        self.yaml_file = yaml_file
        self.test_cases = []
        self.file_pre_login = None  # 文件级前置登录配置
    
    def _translate_keywords(self, data: Any) -> Any:
        """
        将中文关键字转换为英文关键字（优化版本，减少字典查找次数）
        
        Args:
            data: 需要转换的数据
        
        Returns:
            转换后的数据
        """
        if isinstance(data, dict):
            # 使用字典推导式，性能更好
            translated = {
                self.KEYWORD_MAPPING.get(key, key): self._translate_keywords(value)
                for key, value in data.items()
            }
            return translated
        elif isinstance(data, list):
            # 使用列表推导式
            return [self._translate_keywords(item) for item in data]
        else:
            return data
    
    def parse(self) -> List[Dict[str, Any]]:
        """
        解析YAML文件，支持中文关键字和文件级配置
        
        Returns:
            测试用例列表
        """
        if not os.path.exists(self.yaml_file):
            raise FileNotFoundError(f"测试用例文件不存在: {self.yaml_file}")
        
        with open(self.yaml_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        if not content:
            raise ValueError("YAML文件内容为空")
        
        raw_cases = []
        
        if isinstance(content, dict):
            # 检查是否有文件级前置登录配置
            if '前置登录' in content or 'pre_login' in content:
                # 提取文件级前置登录配置
                self.file_pre_login = self._translate_keywords(
                    content.get('前置登录') or content.get('pre_login')
                )
                # 提取用例列表
                raw_cases = content.get('用例列表') or content.get('test_cases', [])
                if not raw_cases:
                    # 如果没有用例列表，尝试从其他字段提取用例
                    # 移除配置字段，剩余的可能是一个或多个用例
                    content_without_config = {k: v for k, v in content.items() 
                                            if k not in ['前置登录', 'pre_login', '用例列表', 'test_cases']}
                    if content_without_config:
                        # 如果只有一个字段，可能是单个用例
                        if len(content_without_config) == 1:
                            raw_cases = [list(content_without_config.values())[0]]
                        else:
                            # 多个字段，都当作用例
                            raw_cases = [v for v in content_without_config.values() if isinstance(v, dict)]
            elif '文件配置' in content or 'file_config' in content:
                # 文件配置格式
                file_config = content.get('文件配置') or content.get('file_config')
                file_config_translated = self._translate_keywords(file_config)
                self.file_pre_login = file_config_translated.get('pre_login')
                # 提取用例列表
                raw_cases = content.get('用例列表') or content.get('test_cases', [])
            else:
                # 纯用例格式（单个用例）
                raw_cases = [content]
        elif isinstance(content, list):
            # 纯用例列表格式
            raw_cases = content
        
        # 转换中文关键字为英文关键字
        self.test_cases = [self._translate_keywords(case) for case in raw_cases]
        
        return self.test_cases
    
    def get_file_pre_login(self) -> Dict[str, Any]:
        """
        获取文件级前置登录配置
        
        Returns:
            文件级前置登录配置，如果没有则返回None
        """
        return self.file_pre_login
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """获取解析后的测试用例"""
        return self.test_cases

