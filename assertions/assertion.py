"""
断言模块
支持状态码和响应字段断言
"""
from typing import Dict, Any, List
import json


class Assertion:
    """断言类"""
    
    @staticmethod
    def assert_status_code(response, expected_status: int):
        """
        断言状态码
        
        Args:
            response: 响应对象
            expected_status: 期望的状态码
        
        Raises:
            AssertionError: 状态码不匹配时抛出异常
        """
        actual_status = response.status_code
        assert actual_status == expected_status, \
            f"状态码断言失败: 期望 {expected_status}, 实际 {actual_status}"
    
    @staticmethod
    def _resolve_field_path(data: Any, field_path: str, error_context: str = None) -> Any:
        """
        解析嵌套字段路径（辅助方法，与http_client保持一致）
        
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
                raise ValueError(f"无法解析引用路径: {error_msg}，字段 {key} 不存在")
        return value
    
    @staticmethod
    def _resolve_request_reference(
        expected_value: Any, 
        request_context: Dict[str, Any] = None,
        response_cache: Dict[str, Any] = None
    ) -> Any:
        """
        解析请求参数引用和接口依赖变量
        支持 ${request.json.field} 和 ${用例名称.字段} 格式
        
        Args:
            expected_value: 期望值，可能包含请求参数引用或接口依赖变量
            request_context: 请求上下文，包含json、data、params、headers
            response_cache: 接口响应缓存，用于解析 ${用例名称.字段} 格式
        
        Returns:
            解析后的值
        """
        if not isinstance(expected_value, str) or not expected_value.startswith('${') or not expected_value.endswith('}'):
            return expected_value
        
        # 去掉 ${ 和 }
        ref_path = expected_value[2:-1]
        
            # 支持 ${request.json.field} 格式
        if ref_path.startswith('request.'):
            if request_context is None:
                return expected_value
            
            # 去掉 request. (8个字符)
            ref_path = ref_path[8:]
            
            # 分割请求类型和字段路径
            parts = ref_path.split('.', 1)
            
            if len(parts) == 2:
                request_type, field_path = parts
                request_data = request_context.get(request_type, {})
                
                if isinstance(request_data, dict):
                    # 使用统一的字段路径解析方法
                    return Assertion._resolve_field_path(request_data, field_path, ref_path)
                else:
                    raise ValueError(f"请求参数类型 {request_type} 不是字典类型")
            else:
                raise ValueError(f"请求参数引用格式错误: {expected_value}，应为 ${request.json.field} 格式")
        
        # 支持 ${用例名称.字段} 格式（接口依赖变量）
        elif response_cache is not None:
            parts = ref_path.split('.', 1)
            if len(parts) == 2:
                ref_case_name, field_path = parts
                if ref_case_name in response_cache:
                    ref_response = response_cache[ref_case_name]
                    # 使用统一的字段路径解析方法
                    return Assertion._resolve_field_path(ref_response, field_path, ref_path)
                else:
                    raise ValueError(f"找不到用例响应缓存: {ref_case_name}")
            else:
                raise ValueError(f"接口依赖变量格式错误: {expected_value}，应为 ${用例名称.字段} 格式")
        
        return expected_value
    
    @staticmethod
    def assert_response_field(
        response,
        field_path: str,
        expected_value: Any = None,
        not_empty: bool = False,
        request_context: Dict[str, Any] = None,
        response_cache: Dict[str, Any] = None
    ):
        """
        断言响应字段
        
        Args:
            response: 响应对象
            field_path: 字段路径，支持嵌套，如 data.user.name
            expected_value: 期望值（可选）
            not_empty: 是否断言字段不为空
        
        Raises:
            AssertionError: 断言失败时抛出异常
        """
        try:
            # 优先使用已解析的JSON（从http_client附加的_parsed_json）
            if hasattr(response, '_parsed_json'):
                response_data = response._parsed_json
            elif hasattr(response, 'json'):
                response_data = response.json()
            elif isinstance(response, dict):
                response_data = response
            else:
                response_data = json.loads(response)
        except:
            raise AssertionError(f"无法解析响应为JSON: {response}")
        
        # 解析嵌套字段路径
        keys = field_path.split('.')
        value = response_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                raise AssertionError(f"字段路径不存在: {field_path}")
        
        # 断言不为空
        if not_empty:
            assert value is not None, f"字段 {field_path} 为空"
            if isinstance(value, str):
                assert value.strip() != '', f"字段 {field_path} 为空字符串"
            elif isinstance(value, (list, dict)):
                assert len(value) > 0, f"字段 {field_path} 为空列表或字典"
        
        # 断言期望值
        if expected_value is not None:
            # 解析请求参数引用和接口依赖变量
            resolved_expected_value = Assertion._resolve_request_reference(
                expected_value, request_context, response_cache
            )
            # 打印实际值用于调试
            print(f"    实际值 = {value}")
            assert value == resolved_expected_value, \
                f"字段 {field_path} 断言失败: 期望 {resolved_expected_value}, 实际 {value}"
    
    @staticmethod
    def assert_response_not_empty(response, field_path: str = None):
        """
        断言响应或字段不为空
        
        Args:
            response: 响应对象
            field_path: 字段路径（可选），如果不提供则断言整个响应
        
        Raises:
            AssertionError: 断言失败时抛出异常
        """
        if field_path:
            Assertion.assert_response_field(response, field_path, not_empty=True)
        else:
            try:
                # 优先使用已解析的JSON（从http_client附加的_parsed_json）
                if hasattr(response, '_parsed_json'):
                    response_data = response._parsed_json
                elif hasattr(response, 'json'):
                    response_data = response.json()
                elif isinstance(response, dict):
                    response_data = response
                else:
                    response_data = json.loads(response)
                
                assert response_data is not None, "响应为空"
                if isinstance(response_data, dict):
                    assert len(response_data) > 0, "响应为空字典"
                elif isinstance(response_data, list):
                    assert len(response_data) > 0, "响应为空列表"
            except json.JSONDecodeError:
                # 如果不是JSON，检查文本内容
                if hasattr(response, 'text'):
                    assert response.text.strip() != '', "响应文本为空"
                else:
                    assert str(response).strip() != '', "响应为空"
    
    @staticmethod
    def assert_multiple_fields(
        response,
        assertions: List[Dict[str, Any]],
        request_context: Dict[str, Any] = None,
        response_cache: Dict[str, Any] = None
    ):
        """
        批量断言多个字段
        
        Args:
            response: 响应对象
            assertions: 断言配置列表，每个配置包含:
                - field: 字段路径
                - expected_value: 期望值（可选）
                - not_empty: 是否断言不为空（可选）
            request_context: 请求上下文
            response_cache: 接口响应缓存，用于解析 ${用例名称.字段} 格式
        
        Raises:
            AssertionError: 断言失败时抛出异常
        """
        for assertion in assertions:
            field = assertion.get('field')
            expected_value = assertion.get('expected_value')
            not_empty = assertion.get('not_empty', False)
            
            # 检查是否明确设置了expected_value（包括None/null）
            # 使用 'expected_value' in assertion 来判断是否明确设置了值
            has_expected_value = 'expected_value' in assertion
            
            # 解析期望值中的变量引用（如果期望值不是None）
            if expected_value is not None:
                expected_value = Assertion._resolve_request_reference(
                    expected_value, request_context, response_cache
                )
            
            # 打印断言信息
            if not_empty:
                print(f"  ✓ 断言字段 {field} 不为空")
                Assertion.assert_response_field(
                    response, field, not_empty=True, 
                    request_context=request_context,
                    response_cache=response_cache
                )
            elif has_expected_value:
                # 明确设置了期望值（包括None/null）
                print(f"  ✓ 断言字段 {field}: 期望值 = {expected_value}")
                Assertion.assert_response_field(
                    response, field, expected_value=expected_value, 
                    request_context=request_context,
                    response_cache=response_cache
                )
            else:
                # 既没有设置期望值，也没有设置不为空，默认断言不为空
                print(f"  ✓ 断言字段 {field} 不为空")
                Assertion.assert_response_field(
                    response, field, not_empty=True, 
                    request_context=request_context,
                    response_cache=response_cache
                )

