"""
YAML用例格式验证器
在运行前检查用例格式是否正确
"""
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.exceptions import ValidationError


class YamlValidator:
    """YAML用例格式验证器"""
    
    # 必填字段
    REQUIRED_FIELDS = ['name', 'method', 'url']
    
    # 字段类型定义
    FIELD_TYPES = {
        'name': str,
        'description': str,
        'method': str,
        'url': str,
        'headers': dict,
        'params': dict,
        'json': dict,
        'data': (str, dict),
        'pre_sql': str,
        'post_sql': str,
        'pre_login': dict,
        'no_token': bool,
        'assertions': dict,
    }
    
    # 允许的HTTP方法
    ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
    
    def __init__(self, yaml_file: str):
        """
        初始化验证器
        
        Args:
            yaml_file: YAML文件路径
        """
        self.yaml_file = yaml_file
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> bool:
        """
        验证YAML文件格式
        
        Returns:
            是否验证通过
        
        Raises:
            ValidationError: 验证失败时抛出
        """
        self.errors.clear()
        self.warnings.clear()
        
        # 检查文件是否存在
        if not Path(self.yaml_file).exists():
            raise ValidationError(f"用例文件不存在: {self.yaml_file}")
        
        # 解析YAML文件
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"YAML格式错误: {e}")
        except Exception as e:
            raise ValidationError(f"读取文件失败: {e}")
        
        if not content:
            raise ValidationError("YAML文件内容为空")
        
        # 验证文件结构
        self._validate_structure(content)
        
        # 验证用例列表
        test_cases = self._extract_test_cases(content)
        for index, case in enumerate(test_cases, 1):
            self._validate_test_case(case, index)
        
        # 如果有错误，抛出异常
        if self.errors:
            error_msg = f"用例文件验证失败 ({self.yaml_file}):\n" + "\n".join(f"  {i+1}. {e}" for i, e in enumerate(self.errors))
            raise ValidationError(error_msg)
        
        # 如果有警告，记录但不阻止执行
        if self.warnings:
            for warning in self.warnings:
                print(f"⚠️  警告: {warning}")
        
        return True
    
    def _validate_structure(self, content: Dict[str, Any]):
        """验证文件结构"""
        # 检查是否有用例列表或前置登录配置
        if 'test_cases' not in content and not isinstance(content, list):
            # 可能是旧格式，尝试作为用例列表处理
            if isinstance(content, list):
                return
            else:
                self.errors.append("文件结构错误：缺少 '用例列表' 或用例数组")
    
    def _extract_test_cases(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取测试用例列表"""
        # 新格式：有 test_cases 字段
        if 'test_cases' in content:
            test_cases = content['test_cases']
            if not isinstance(test_cases, list):
                self.errors.append("'用例列表' 必须是数组")
                return []
            return test_cases
        
        # 旧格式：直接是用例数组
        if isinstance(content, list):
            return content
        
        return []
    
    def _validate_test_case(self, case: Dict[str, Any], index: int):
        """验证单个测试用例"""
        case_name = case.get('name', f'用例{index}')
        
        # 验证必填字段
        for field in self.REQUIRED_FIELDS:
            if field not in case:
                self.errors.append(f"用例 '{case_name}': 缺少必填字段 '{field}'")
        
        # 验证字段类型
        for field, expected_type in self.FIELD_TYPES.items():
            if field in case:
                value = case[field]
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        self.errors.append(
                            f"用例 '{case_name}': 字段 '{field}' 类型错误，"
                            f"期望 {expected_type}，实际 {type(value).__name__}"
                        )
                elif not isinstance(value, expected_type):
                    self.errors.append(
                        f"用例 '{case_name}': 字段 '{field}' 类型错误，"
                        f"期望 {expected_type.__name__}，实际 {type(value).__name__}"
                    )
        
        # 验证HTTP方法
        method = case.get('method', '').upper()
        if method and method not in self.ALLOWED_METHODS:
            self.errors.append(
                f"用例 '{case_name}': HTTP方法 '{method}' 不支持，"
                f"允许的方法: {', '.join(self.ALLOWED_METHODS)}"
            )
        
        # 验证URL
        url = case.get('url', '')
        if url and not isinstance(url, str):
            self.errors.append(f"用例 '{case_name}': URL 必须是字符串")
        
        # 验证断言配置
        assertions = case.get('assertions')
        if assertions:
            self._validate_assertions(assertions, case_name)
        
        # 验证前置登录配置
        pre_login = case.get('pre_login')
        if pre_login:
            self._validate_pre_login(pre_login, case_name)
    
    def _validate_assertions(self, assertions: Dict[str, Any], case_name: str):
        """验证断言配置"""
        # 验证状态码
        status_code = assertions.get('status_code')
        if status_code is not None and not isinstance(status_code, int):
            self.errors.append(f"用例 '{case_name}': 断言状态码必须是整数")
        
        # 验证字段断言
        fields = assertions.get('fields', [])
        if not isinstance(fields, list):
            self.errors.append(f"用例 '{case_name}': 字段断言必须是数组")
        else:
            for i, field_assert in enumerate(fields):
                if not isinstance(field_assert, dict):
                    self.errors.append(f"用例 '{case_name}': 字段断言[{i}] 必须是对象")
                elif 'field' not in field_assert:
                    self.errors.append(f"用例 '{case_name}': 字段断言[{i}] 缺少 'field' 字段")
    
    def _validate_pre_login(self, pre_login: Dict[str, Any], case_name: str):
        """验证前置登录配置"""
        if not isinstance(pre_login, dict):
            self.errors.append(f"用例 '{case_name}': 前置登录配置必须是对象")
            return
        
        # 如果启用自动注册，需要用户名、密码、邮箱
        if pre_login.get('auto_register'):
            required_fields = ['username', 'password']
            for field in required_fields:
                if field not in pre_login:
                    self.errors.append(
                        f"用例 '{case_name}': 前置登录启用自动注册时，"
                        f"必须配置 '{field}'"
                    )
        
        # 如果使用自定义登录，需要登录接口和方法
        if not pre_login.get('auto_register') and not pre_login.get('login_url'):
            self.warnings.append(
                f"用例 '{case_name}': 前置登录配置可能不完整，"
                f"建议配置 'login_url' 或启用 'auto_register'"
            )


def validate_yaml_file(yaml_file: str) -> bool:
    """
    验证YAML用例文件格式（便捷函数）
    
    Args:
        yaml_file: YAML文件路径
    
    Returns:
        是否验证通过
    
    Raises:
        ValidationError: 验证失败时抛出
    """
    validator = YamlValidator(yaml_file)
    return validator.validate()
