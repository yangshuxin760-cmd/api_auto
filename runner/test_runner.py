"""
测试运行器
支持接口依赖、SQL操作和断言
"""
import allure
from typing import Dict, Any, List
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.yaml_parser import YamlParser
from request.http_client import HttpClient
from assertions.assertion import Assertion
from database.db_handler import DatabaseHandler


class TestRunner:
    """测试运行器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化测试运行器
        
        Args:
            config_path: 配置文件路径
        """
        self.http_client = HttpClient(config_path)
        self.db_handler = DatabaseHandler(config_path)
        self.assertion = Assertion()
    
    def _execute_pre_sql(self, sql: str) -> Any:
        """
        执行前置SQL
        
        Args:
            sql: SQL语句
        
        Returns:
            SQL执行结果
        """
        if sql:
            result = self.db_handler.execute_pre_sql(sql)
            return result
        return None
    
    def _execute_post_sql(self, sql: str):
        """
        执行后置SQL
        
        Args:
            sql: SQL语句
        """
        if sql:
            self.db_handler.execute_post_sql(sql)
    
    def _resolve_sql_result(self, data: Any, sql_result: Any) -> Any:
        """
        将SQL结果解析到接口参数中
        
        Args:
            data: 接口参数
            sql_result: SQL执行结果
        
        Returns:
            解析后的参数
        """
        if sql_result is None:
            return data
        
        if isinstance(data, dict):
            resolved = {}
            for key, value in data.items():
                if isinstance(value, str) and value.startswith('${sql.'):
                    # 支持 ${sql.field} 格式引用SQL结果
                    field_name = value[6:-1]  # 去掉 ${sql. 和 }
                    if isinstance(sql_result, dict) and field_name in sql_result:
                        resolved[key] = sql_result[field_name]
                    else:
                        resolved[key] = value
                else:
                    resolved[key] = self._resolve_sql_result(value, sql_result)
            return resolved
        elif isinstance(data, list):
            return [self._resolve_sql_result(item, sql_result) for item in data]
        elif isinstance(data, str) and data.startswith('${sql.'):
            field_name = data[6:-1]
            if isinstance(sql_result, dict) and field_name in sql_result:
                return sql_result[field_name]
        return data
    
    def _run_test_case(self, test_case: Dict[str, Any]) -> bool:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例配置
        
        Returns:
            是否执行成功
        """
        case_name = test_case.get('name', '未命名用例')
        case_description = test_case.get('description', '')
        
        # 打印用例开始分隔符
        print(f"\n{'#' * 100}")
        print(f"🚀 开始执行用例: {case_name}")
        if case_description:
            print(f"📝 描述: {case_description}")
        print(f"{'#' * 100}\n")
        
        with allure.step(f"执行用例: {case_name}"):
            if case_description:
                allure.dynamic.description(case_description)
            
            try:
                # 执行前置SQL
                pre_sql = test_case.get('pre_sql')
                sql_result = None
                if pre_sql:
                    with allure.step("执行前置SQL"):
                        allure.attach(pre_sql, "前置SQL", allure.attachment_type.TEXT)
                        sql_result = self._execute_pre_sql(pre_sql)
                        if sql_result:
                            allure.attach(
                                str(sql_result),
                                "SQL执行结果",
                                allure.attachment_type.JSON
                            )
                
                # 准备请求参数
                method = test_case.get('method', 'GET').upper()
                url = test_case.get('url', '')
                headers = test_case.get('headers', {})
                params = test_case.get('params', {})
                data = test_case.get('data')
                json_data = test_case.get('json', {})
                # 是否禁用token（用于未登录场景）
                no_token = test_case.get('no_token', False)
                
                # 解析SQL结果到参数中
                if sql_result:
                    headers = self._resolve_sql_result(headers, sql_result)
                    params = self._resolve_sql_result(params, sql_result)
                    data = self._resolve_sql_result(data, sql_result) if data else None
                    json_data = self._resolve_sql_result(json_data, sql_result) if json_data else {}
                
                # 解析变量（如${timestamp}）到参数中，包括URL
                url = self.http_client._resolve_variables(url, case_name) if url else ''
                headers = self.http_client._resolve_variables(headers, case_name) if headers else {}
                params = self.http_client._resolve_variables(params, case_name) if params else {}
                data = self.http_client._resolve_variables(data, case_name) if data else None
                json_data = self.http_client._resolve_variables(json_data, case_name) if json_data else {}
                
                # 发送请求
                with allure.step(f"发送{method}请求"):
                    allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                    if headers:
                        allure.attach(
                            str(headers),
                            "请求头",
                            allure.attachment_type.JSON
                        )
                    if params:
                        allure.attach(
                            str(params),
                            "URL参数",
                            allure.attachment_type.JSON
                        )
                    if json_data:
                        allure.attach(
                            str(json_data),
                            "请求体(JSON)",
                            allure.attachment_type.JSON
                        )
                    if data:
                        allure.attach(
                            str(data),
                            "请求体(Form)",
                            allure.attachment_type.TEXT
                        )
                    
                    response = self.http_client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        data=data,
                        json_data=json_data,
                        case_name=case_name,
                        use_token=not no_token
                    )
                    
                    # 记录响应
                    try:
                        response_json = response.json()
                        allure.attach(
                            str(response_json),
                            "响应内容",
                            allure.attachment_type.JSON
                        )
                    except:
                        allure.attach(
                            response.text,
                            "响应内容",
                            allure.attachment_type.TEXT
                        )
                    
                    allure.attach(
                        str(response.status_code),
                        "状态码",
                        allure.attachment_type.TEXT
                    )
                
                # 执行断言
                assertions = test_case.get('assertions', {})
                
                # 准备请求参数上下文（用于断言中引用请求参数）
                request_context = {
                    'json': json_data if json_data else {},
                    'data': data if data else {},
                    'params': params if params else {},
                    'headers': headers if headers else {}
                }
                
                # 断言状态码
                expected_status = assertions.get('status_code')
                if expected_status:
                    with allure.step(f"断言状态码: {expected_status}"):
                        self.assertion.assert_status_code(response, expected_status)
                
                # 断言响应字段
                fields = assertions.get('fields', [])
                if fields:
                    with allure.step("断言响应字段"):
                        self.assertion.assert_multiple_fields(
                            response, fields, 
                            request_context=request_context,
                            response_cache=self.http_client.response_cache
                        )
                
                # 断言响应不为空
                if assertions.get('not_empty', False):
                    with allure.step("断言响应不为空"):
                        self.assertion.assert_response_not_empty(response)
                
                # 执行后置SQL
                post_sql = test_case.get('post_sql')
                if post_sql:
                    with allure.step("执行后置SQL"):
                        allure.attach(post_sql, "后置SQL", allure.attachment_type.TEXT)
                        self._execute_post_sql(post_sql)
                
                # 打印用例成功标记
                print(f"✅ 用例执行成功\n")
                return True
                
            except AssertionError as e:
                print(f"❌ 用例断言失败: {str(e)}\n")
                allure.attach(
                    str(e),
                    "断言失败",
                    allure.attachment_type.TEXT
                )
                raise
            except Exception as e:
                print(f"❌ 用例执行异常: {str(e)}\n")
                allure.attach(
                    str(e),
                    "执行异常",
                    allure.attachment_type.TEXT
                )
                raise
    
    def run(self, yaml_file: str):
        """
        运行测试用例
        
        Args:
            yaml_file: YAML测试用例文件路径
        """
        parser = YamlParser(yaml_file)
        test_cases = parser.parse()
        
        total_cases = len(test_cases)
        passed_cases = 0
        failed_cases = 0
        
        try:
            for index, test_case in enumerate(test_cases, 1):
                case_name = test_case.get('name', '未命名用例')
                try:
                    print(f"\n[{index}/{total_cases}] 执行用例: {case_name}")
                    self._run_test_case(test_case)
                    passed_cases += 1
                    print(f"✓ 用例执行成功: {case_name}")
                except AssertionError as e:
                    failed_cases += 1
                    print(f"✗ 用例断言失败: {case_name}")
                    print(f"  错误信息: {str(e)}")
                    # 继续执行下一个用例，不中断
                    continue
                except Exception as e:
                    failed_cases += 1
                    print(f"✗ 用例执行异常: {case_name}")
                    print(f"  错误信息: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # 继续执行下一个用例，不中断
                    continue
            
            # 打印执行总结
            print(f"\n{'='*60}")
            print(f"测试执行完成:")
            print(f"  总用例数: {total_cases}")
            print(f"  通过: {passed_cases}")
            print(f"  失败: {failed_cases}")
            print(f"{'='*60}")
            
        finally:
            # 关闭数据库连接
            self.db_handler.disconnect()

