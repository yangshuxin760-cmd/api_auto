"""
HTTP请求客户端
支持token自动传递和接口依赖
"""
import requests
from typing import Dict, Any, Optional
import yaml
import os
import json
import logging
import time
import random
import uuid

# 配置日志（避免重复配置）
logger = logging.getLogger('HttpClient')
if not logger.handlers:  # 避免重复添加处理器
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 防止日志向上传播导致重复


class HttpClient:
    """HTTP请求客户端"""
    
    def __init__(self, config_path: str = None):
        """
        初始化HTTP客户端
        
        Args:
            config_path: 配置文件路径（已废弃，保留以兼容旧代码）
        """
        from config.config_manager import get_config
        
        self.session = requests.Session()
        self.token = None
        self.response_cache = {}  # 存储接口响应，用于依赖引用
        
        # 使用统一的配置管理器
        self.config = get_config(config_path)
        self.base_url = self.config.get_base_url()
        self.timeout = self.config.get_timeout()
        self.token_config = self.config.get_token_config()
        self.default_headers = self.config.get_default_headers()
    
    def set_token(self, token: str):
        """
        设置token
        
        Args:
            token: token值
        """
        self.token = token
    
    def _get_token_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """
        从响应中提取token
        
        Args:
            response: 响应数据
        
        Returns:
            token值
        """
        field_path = self.token_config.get('field_path', '')
        if not field_path:
            return None
        
        # 支持嵌套字段路径，如 data.token
        keys = field_path.split('.')
        value = response
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return str(value) if value else None
    
    def _add_token_to_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加token到请求头
        
        Args:
            headers: 原始请求头
        
        Returns:
            添加token后的请求头
        """
        if headers is None:
            headers = {}
        
        if self.token:
            header_key = self.token_config.get('header_key', 'Authorization')
            prefix = self.token_config.get('prefix', '')
            
            if prefix:
                token_value = f"{prefix} {self.token}"
            else:
                token_value = self.token
            
            headers[header_key] = token_value
        
        return headers

    def _merge_headers(
        self,
        base_headers: Optional[Dict[str, Any]],
        override_headers: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        合并请求头（override 覆盖 base，同名 key 以 override 为准）
        """
        if not base_headers and not override_headers:
            return None
        merged: Dict[str, Any] = {}
        if isinstance(base_headers, dict):
            merged.update(base_headers)
        if isinstance(override_headers, dict):
            merged.update(override_headers)
        return merged
    
    def _resolve_field_path(self, data: Any, field_path: str, error_context: str = None) -> Any:
        """
        解析嵌套字段路径（辅助方法，减少重复代码）
        
        Args:
            data: 数据对象（dict或list）
            field_path: 字段路径，如 "data.user.name" 或 "0.id"
            error_context: 错误上下文，用于错误信息
        
        Returns:
            解析后的值
        
        Raises:
            ValueError: 路径不存在时抛出异常
        """
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                error_msg = error_context or field_path
                raise ValueError(f"无法解析引用路径: {error_msg}")
        return value
    
    def _resolve_builtin_variables(self, var_name: str) -> str:
        """
        解析内置变量（使用字典映射优化性能）
        
        Args:
            var_name: 变量名称
        
        Returns:
            变量值
        """
        # 使用字典映射替代多个if-elif，提高性能
        builtin_handlers = {
            'timestamp': lambda: str(int(time.time())),
            'timestamp_ms': lambda: str(int(time.time() * 1000)),
            'random': lambda: str(random.randint(0, 999999)),
            'random_int': lambda: str(random.randint(0, 999999)),
            'uuid': lambda: str(uuid.uuid4()),
            'uuid_short': lambda: str(uuid.uuid4()).replace('-', '')
        }
        
        handler = builtin_handlers.get(var_name)
        if handler:
            return handler()
            return None
    
    def _resolve_variables(self, data: Any, case_name: str = None) -> Any:
        """
        解析变量引用，支持引用前置接口的响应数据和内置变量
        
        Args:
            data: 需要解析的数据
            case_name: 当前用例名称
        
        Returns:
            解析后的数据
        """
        if isinstance(data, dict):
            resolved = {}
            for key, value in data.items():
                resolved[key] = self._resolve_variables(value, case_name)
            return resolved
        elif isinstance(data, list):
            return [self._resolve_variables(item, case_name) for item in data]
        elif isinstance(data, str):
            # 支持 ${variable} 格式的引用
            if data.startswith('${') and data.endswith('}'):
                ref_path = data[2:-1]  # 去掉 ${ 和 }
                
                # 首先尝试解析内置变量
                builtin_value = self._resolve_builtin_variables(ref_path)
                if builtin_value is not None:
                    return builtin_value
                
                # 支持 ${redis.xxx} 格式（Redis查询，由test_runner处理，这里跳过）
                if ref_path.startswith('redis.'):
                    return data  # 返回原值，让test_runner处理
                
                # 支持 ${sql.xxx} 格式（SQL查询结果，由test_runner处理，这里跳过）
                if ref_path.startswith('sql.'):
                    return data  # 返回原值，让test_runner处理
                
                # 支持 ${case_name.field} 格式的引用
                parts = ref_path.split('.', 1)
                if len(parts) == 2:
                    ref_case_name, field_path = parts
                    if ref_case_name in self.response_cache:
                        ref_response = self.response_cache[ref_case_name]
                        
                        # 解析嵌套字段路径（提取为辅助方法，减少重复）
                        return self._resolve_field_path(ref_response, field_path, ref_path)
                    else:
                        raise ValueError(f"引用的用例响应不存在: {ref_case_name}")
                else:
                    # 如果没有指定用例名，尝试从当前用例的响应中查找
                    if case_name and case_name in self.response_cache:
                        ref_response = self.response_cache[case_name]
                        return self._resolve_field_path(ref_response, ref_path, ref_path)
                    else:
                        # 如果都不是，尝试作为内置变量
                        builtin_value = self._resolve_builtin_variables(ref_path)
                        if builtin_value is not None:
                            return builtin_value
                        raise ValueError(f"无法解析变量: {ref_path}")
            
            # 支持在字符串中嵌入变量，如 "autotest_${timestamp}"
            if '${' in data and '}' in data:
                import re
                pattern = r'\$\{([^}]+)\}'
                def replace_var(match):
                    var_name = match.group(1)
                    # 尝试解析内置变量
                    builtin_value = self._resolve_builtin_variables(var_name)
                    if builtin_value is not None:
                        return builtin_value
                    # 跳过 ${redis.xxx} 和 ${sql.xxx} 格式（由test_runner处理）
                    if var_name.startswith('redis.') or var_name.startswith('sql.'):
                        return match.group(0)  # 返回原值
                    
                    # 尝试解析接口依赖变量
                    parts = var_name.split('.', 1)
                    if len(parts) == 2:
                        ref_case_name, field_path = parts
                        if ref_case_name in self.response_cache:
                            ref_response = self.response_cache[ref_case_name]
                            try:
                                value = self._resolve_field_path(ref_response, field_path, var_name)
                                return str(value)
                            except:
                                    return match.group(0)  # 无法解析，返回原值
                    return match.group(0)  # 无法解析，返回原值
                
                return re.sub(pattern, replace_var, data)
            
            return data
        else:
            return data
    
    def request(
        self,
        method: str,
        url: str,
        headers: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        data: Any = None,
        json_data: Dict[str, Any] = None,
        case_name: str = None,
        use_token: bool = True
    ) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: 请求方法 (GET, POST, PUT, DELETE等)
            url: 请求URL
            headers: 请求头
            params: URL参数
            data: 表单数据
            json_data: JSON数据
            case_name: 用例名称，用于变量解析
        
        Returns:
            响应对象
        """
        # 构建完整URL
        if url.startswith('http://') or url.startswith('https://'):
            full_url = url
        else:
            full_url = f"{self.base_url}{url}"
        
        # 合并全局默认请求头 + 用例请求头（用例优先）
        headers = self._merge_headers(self.default_headers, headers)

        # 解析变量引用
        headers = self._resolve_variables(headers, case_name) if headers else None
        params = self._resolve_variables(params, case_name) if params else None
        data = self._resolve_variables(data, case_name) if data else None
        # 注意：json_data即使是空字典{}也要保留，确保发送JSON请求
        if json_data is not None:
            json_data = self._resolve_variables(json_data, case_name)
        
        # 添加token到请求头（仅当允许使用token时）
        if use_token:
            headers = self._add_token_to_headers(headers)
        
        # 打印请求日志（简洁版）
        start_time = time.time()
        logger.info(f"🌐 {method.upper()} {full_url}")
        if params:
            logger.info(f"📌 参数: {json.dumps(params, ensure_ascii=False)}")
        if json_data is not None:
            logger.info(f"📤 请求: {json.dumps(json_data, ensure_ascii=False)}")
        elif data:
            logger.info(f"📤 表单: {data}")
        
        # 发送请求
        try:
            # 如果json_data是None，不传递json参数；如果是空字典{}，也要传递以发送JSON请求
            request_kwargs = {
                'method': method.upper(),
                'url': full_url,
                'headers': headers,
                'params': params,
                'timeout': self.timeout
            }
            if json_data is not None:
                request_kwargs['json'] = json_data
            elif data:
                request_kwargs['data'] = data
            
            response = self.session.request(**request_kwargs)
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"【请求异常】{str(e)}")
            logger.error(f"【请求耗时】{elapsed_time:.3f}秒")
            logger.error("=" * 80)
            raise
        
        # 计算请求耗时
        elapsed_time = time.time() - start_time
        
        # 解析响应JSON（只解析一次，后续复用）
        response_json = None
        is_json = False
        try:
            response_json = response.json()
            is_json = True
        except:
            pass

        # 状态码和耗时（一行显示）
        status_icon = "❌" if response.status_code >= 400 else "✅"
        logger.info(f"{status_icon} 状态: {response.status_code} | 耗时: {elapsed_time:.3f}秒")
        
        # 响应内容（简洁显示，只显示关键信息）
        if is_json and isinstance(response_json, dict):
            # 优先显示关键字段
            key_fields = ['id', 'username', 'email', 'message', 'detail', 'code', 'status', 'success', 'token']
            summary_items = []
            for key in key_fields:
                if key in response_json:
                    value = response_json[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    summary_items.append(f"{key}={value}")
            
            if summary_items:
                logger.info(f"📥 响应: {' | '.join(summary_items)}")
            else:
                # 如果没有关键字段，显示前3个字段
                items = list(response_json.items())[:3]
                if items:
                    logger.info(f"📥 响应: {json.dumps(dict(items), ensure_ascii=False)}")
        elif is_json:
            # 如果是数组或其他类型，显示前100个字符
            response_str = json.dumps(response_json, ensure_ascii=False)
            if len(response_str) > 100:
                response_str = response_str[:100] + "..."
            logger.info(f"📥 响应: {response_str}")
        else:
            # 非JSON响应，显示前100个字符
            response_text = response.text[:100] + "..." if len(response.text) > 100 else response.text
            logger.info(f"📥 响应: {response_text}")
        
        # 尝试从响应中提取token（使用已解析的JSON）
        if is_json and response_json:
            token = self._get_token_from_response(response_json)
            if token:
                self.set_token(token)
        
        # 缓存响应数据，用于后续接口依赖（使用已解析的JSON）
        # 同时将解析后的JSON附加到response对象，避免重复解析
        if case_name:
            if is_json and response_json:
                self.response_cache[case_name] = response_json
            else:
                self.response_cache[case_name] = {'text': response.text}
        
        # 将解析后的JSON附加到response对象，供后续使用
        if is_json and response_json:
            response._parsed_json = response_json
        
        return response
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST请求"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """PUT请求"""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE请求"""
        return self.request('DELETE', url, **kwargs)

