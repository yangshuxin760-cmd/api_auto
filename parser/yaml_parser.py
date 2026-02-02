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
    
    def _translate_keywords(self, data: Any) -> Any:
        """
        将中文关键字转换为英文关键字
        
        Args:
            data: 需要转换的数据
        
        Returns:
            转换后的数据
        """
        if isinstance(data, dict):
            translated = {}
            for key, value in data.items():
                # 转换键名
                translated_key = self.KEYWORD_MAPPING.get(key, key)
                # 递归转换值
                translated[translated_key] = self._translate_keywords(value)
            return translated
        elif isinstance(data, list):
            return [self._translate_keywords(item) for item in data]
        else:
            return data
    
    def parse(self) -> List[Dict[str, Any]]:
        """
        解析YAML文件，支持中文关键字
        
        Returns:
            测试用例列表
        """
        if not os.path.exists(self.yaml_file):
            raise FileNotFoundError(f"测试用例文件不存在: {self.yaml_file}")
        
        with open(self.yaml_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        if not content:
            raise ValueError("YAML文件内容为空")
        
        # 支持单个用例或多个用例
        if isinstance(content, list):
            raw_cases = content
        else:
            raw_cases = [content]
        
        # 转换中文关键字为英文关键字
        self.test_cases = [self._translate_keywords(case) for case in raw_cases]
        
        return self.test_cases
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """获取解析后的测试用例"""
        return self.test_cases

