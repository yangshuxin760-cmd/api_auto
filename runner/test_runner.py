"""
测试运行器
支持接口依赖、SQL操作和断言
"""
import allure
import time
from typing import Dict, Any, List, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser.yaml_parser import YamlParser
from request.http_client import HttpClient
from assertions.assertion import Assertion
from database.db_handler import DatabaseHandler
from redis_handler.redis_handler import RedisHandler


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
        self.redis_handler = RedisHandler(config_path)
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
    
    def _execute_pre_login(self, pre_login_config: Dict[str, Any], case_name: str):
        """
        执行前置登录，为当前用例获取独立的登录token
        
        Args:
            pre_login_config: 前置登录配置
            case_name: 当前用例名称
        """
        import allure
        
        # 获取登录配置
        auto_register = pre_login_config.get('auto_register', False)
        username = pre_login_config.get('username', f'test_user_{int(time.time())}')
        password = pre_login_config.get('password', 'testpass123')
        login_url = pre_login_config.get('login_url', '/login')
        login_method = pre_login_config.get('login_method', 'POST').upper()
        login_body = pre_login_config.get('login_body', {})
        
        # 解析变量（如${timestamp}）
        username = self.http_client._resolve_variables(username, case_name) if isinstance(username, str) else username
        password = self.http_client._resolve_variables(password, case_name) if isinstance(password, str) else password
        
        # 如果配置了自动注册，先注册账号
        if auto_register:
            with allure.step("自动注册账号"):
                register_url = pre_login_config.get('register_url', '/register')
                register_email = pre_login_config.get('email', f'{username}@test.com')
                
                # 解析邮箱变量
                register_email = self.http_client._resolve_variables(register_email, case_name) if isinstance(register_email, str) else register_email
                
                register_data = {
                    'username': username,
                    'email': register_email,
                    'password': password
                }
                
                allure.attach(
                    str(register_data),
                    "注册请求",
                    allure.attachment_type.JSON
                )
                
                # 发送注册请求
                register_response = self.http_client.request(
                    method='POST',
                    url=register_url,
                    headers={'Content-Type': 'application/json'},
                    json_data=register_data,
                    case_name=f"{case_name}_注册",
                    use_token=False  # 注册不需要token
                )
                
                allure.attach(
                    str(register_response.status_code),
                    "注册状态码",
                    allure.attachment_type.TEXT
                )
                
                try:
                    register_json = register_response.json()
                    allure.attach(
                        str(register_json),
                        "注册响应",
                        allure.attachment_type.JSON
                    )
                except:
                    allure.attach(
                        register_response.text,
                        "注册响应",
                        allure.attachment_type.TEXT
                    )
                
                if register_response.status_code not in [200, 201]:
                    print(f"⚠️  账号注册失败，状态码: {register_response.status_code}")
                    # 如果注册失败，继续尝试登录（可能账号已存在）
        
        # 准备登录请求体
        if not login_body:
            # 如果没有配置登录请求体，使用默认格式
            login_body = {
                'username': username,
                'password': password
            }
        else:
            # 如果配置了登录请求体，先解析其中的变量
            login_body = self.http_client._resolve_variables(login_body, case_name)
            # 然后替换用户名和密码（支持多种字段名）
            # 支持 username/user/account 等字段名
            for key in ['username', 'user', 'account', 'login']:
                if key in login_body:
                    login_body[key] = username
                    break
            else:
                # 如果都没有，添加username字段
                login_body['username'] = username
            
            # 支持 password/pwd/pass 等字段名
            for key in ['password', 'pwd', 'pass']:
                if key in login_body:
                    login_body[key] = password
                    break
            else:
                # 如果都没有，添加password字段
                login_body['password'] = password
        
        with allure.step("执行登录"):
            allure.attach(
                str(login_body),
                "登录请求",
                allure.attachment_type.JSON
            )
            
            # 发送登录请求（不使用token）
            login_response = self.http_client.request(
                method=login_method,
                url=login_url,
                headers={'Content-Type': 'application/json'},
                json_data=login_body,
                case_name=f"{case_name}_登录",
                use_token=False  # 登录不需要token
            )
            
            allure.attach(
                str(login_response.status_code),
                "登录状态码",
                allure.attachment_type.TEXT
            )
            
            try:
                login_json = login_response.json()
                allure.attach(
                    str(login_json),
                    "登录响应",
                    allure.attachment_type.JSON
                )
            except:
                allure.attach(
                    login_response.text,
                    "登录响应",
                    allure.attachment_type.TEXT
                )
            
            if login_response.status_code == 200:
                # 登录成功，token会自动保存到HttpClient中
                print(f"✅ 前置登录成功，用户名: {username}")
            else:
                raise Exception(f"前置登录失败，状态码: {login_response.status_code}, 响应: {login_response.text}")
    
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
    
    def _execute_pre_redis(self, phone: str, key_pattern: str = None) -> Optional[str]:
        """
        从Redis获取验证码
        
        Args:
            phone: 手机号
            key_pattern: Redis键名模式（可选），如果不提供则使用配置文件中的默认值
        
        Returns:
            验证码（字符串），如果不存在返回None
        """
        try:
            code = self.redis_handler.get_verification_code(phone, key_pattern)
            return code
        except Exception as e:
            print(f"⚠️  从Redis获取验证码失败: {str(e)}")
            return None
    
    def _resolve_redis_result(self, data: Any, redis_result: Any) -> Any:
        """
        将Redis结果解析到接口参数中
        
        Args:
            data: 接口参数
            redis_result: Redis查询结果（验证码字符串）
        
        Returns:
            解析后的参数
        """
        if redis_result is None:
            return data
        
        if isinstance(data, dict):
            resolved = {}
            for key, value in data.items():
                if isinstance(value, str) and value.startswith('${redis.'):
                    # 支持 ${redis.code} 格式引用Redis结果
                    field_name = value[8:-1]  # 去掉 ${redis. 和 }
                    if field_name == 'code':
                        resolved[key] = redis_result
                    else:
                        resolved[key] = value
                else:
                    resolved[key] = self._resolve_redis_result(value, redis_result)
            return resolved
        elif isinstance(data, list):
            return [self._resolve_redis_result(item, redis_result) for item in data]
        elif isinstance(data, str) and data.startswith('${redis.'):
            field_name = data[8:-1]
            if field_name == 'code':
                return redis_result
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
        
        # 打印用例开始分隔符
        CASE_SEPARATOR = '#' * 100
        print(f"\n{CASE_SEPARATOR}")
        print(f"🚀 开始执行用例: {case_name}")
        print(f"{CASE_SEPARATOR}\n")
        
        with allure.step(f"执行用例: {case_name}"):
            
            try:
                # 执行前置登录（如果配置了）
                # 优先级：用例级前置登录 > 文件级前置登录 > 全局token
                pre_login = test_case.get('pre_login')
                if pre_login:
                    with allure.step("执行用例级前置登录"):
                        # 用例级前置登录，获取独立的token（优先级最高）
                        self._execute_pre_login(pre_login, case_name)
                        print(f"用例级前置登录完成，已获取独立token")
                # 如果没有配置用例级前置登录，使用文件级或全局token
                # 如果用例不需要token，可以配置 不使用token: true
                
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
                
                # 解析变量（如${timestamp}）到参数中
                # 注意：${redis.xxx} 和 ${sql.xxx} 格式会被跳过，由后续步骤处理
                url = self.http_client._resolve_variables(url, case_name) if url else ''
                headers = self.http_client._resolve_variables(headers, case_name) if headers else {}
                params = self.http_client._resolve_variables(params, case_name) if params else {}
                data = self.http_client._resolve_variables(data, case_name) if data else None
                json_data = self.http_client._resolve_variables(json_data, case_name) if json_data else {}
                
                # 检查是否需要从Redis获取验证码
                redis_result = None
                redis_key_pattern = None
                # 检查用例中是否配置了Redis key模式
                pre_redis = test_case.get('pre_redis')
                if pre_redis:
                    if isinstance(pre_redis, str):
                        redis_key_pattern = pre_redis
                    elif isinstance(pre_redis, dict):
                        redis_key_pattern = pre_redis.get('redis_key_pattern') or pre_redis.get('key_pattern')
                
                if json_data:
                    # 检查请求体中是否有 ${redis.code} 引用
                    json_str = str(json_data)
                    if '${redis.code}' in json_str or 'redis.code' in json_str:
                        # 从请求体中提取phone（此时phone应该已经解析了其他变量）
                        phone = json_data.get('phone', '')
                        if phone:
                            with allure.step("从Redis获取验证码"):
                                if redis_key_pattern:
                                    allure.attach(f"手机号: {phone}\nRedis键模式: {redis_key_pattern}", "Redis查询", allure.attachment_type.TEXT)
                                else:
                                    allure.attach(f"手机号: {phone}", "Redis查询", allure.attachment_type.TEXT)
                                redis_result = self._execute_pre_redis(phone, redis_key_pattern)
                                if redis_result:
                                    allure.attach(
                                        f"验证码: {redis_result}",
                                        "Redis结果",
                                        allure.attachment_type.TEXT
                                    )
                                    print(f"  ✓ 从Redis获取验证码: {redis_result}")
                                else:
                                    print(f"  ⚠️  Redis中未找到验证码（手机号: {phone}）")
                
                # 解析Redis结果到参数中
                if redis_result:
                    headers = self._resolve_redis_result(headers, redis_result)
                    params = self._resolve_redis_result(params, redis_result)
                    data = self._resolve_redis_result(data, redis_result) if data else None
                    json_data = self._resolve_redis_result(json_data, redis_result) if json_data else {}
                
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
                    
                    # 记录响应（从缓存中获取已解析的JSON，避免重复解析）
                    response_json = None
                    if case_name and case_name in self.http_client.response_cache:
                        cached_response = self.http_client.response_cache[case_name]
                        if isinstance(cached_response, dict) and 'text' not in cached_response:
                            response_json = cached_response
                    
                    if response_json is None:
                        try:
                            response_json = response.json()
                        except:
                            response_json = None
                    
                    if response_json is not None:
                        allure.attach(
                            str(response_json),
                            "响应内容",
                            allure.attachment_type.JSON
                        )
                    else:
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
                        print(f"  ✓ 断言状态码: 期望值 = {expected_status}")
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

