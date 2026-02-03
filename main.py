"""
主入口文件
可以直接执行测试
"""
import os
import sys
import pytest
import allure
import time
import json
from datetime import datetime
from runner.test_runner import TestRunner
from report.report_generator import ReportGenerator
from report.dingtalk_notifier import DingTalkNotifier
from config.config_manager import get_config, ConfigError
from utils.logger import init_logger_from_config, get_logger
from utils.exceptions import TestFrameworkError

# 常量定义
STATS_FILE = '.test_stats.json'
STATS_WRITE_INTERVAL = 10  # 统计信息批量写入间隔（每N个用例写入一次）
SEPARATOR_LINE = '=' * 80  # 分隔线

# 初始化日志系统
logger = get_logger(__name__)


def get_yaml_files(path: str) -> list:
    """
    获取YAML测试文件列表
    
    Args:
        path: 文件或目录路径
    
    Returns:
        YAML文件列表
    """
    yaml_files = []
    if os.path.isfile(path):
        if path.endswith('.yaml') or path.endswith('.yml'):
            yaml_files.append(path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    yaml_files.append(os.path.join(root, file))
    return yaml_files


# 存储要运行的YAML文件（全局变量）
_yaml_files_to_run = []

# 存储测试执行开始时间和统计信息（用于钉钉通知）
_test_start_time = None
_test_stats = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'error': 0
}


def pytest_generate_tests(metafunc):
    """
    pytest钩子函数，动态生成测试参数
    """
    if "yaml_file" in metafunc.fixturenames:
        # 如果_yaml_files_to_run为空，尝试从环境变量获取
        if not _yaml_files_to_run:
            import os
            yaml_files_env = os.environ.get('YAML_TEST_FILES', '')
            if yaml_files_env:
                _yaml_files_to_run.extend(yaml_files_env.split(','))
        
        if _yaml_files_to_run:
            metafunc.parametrize("yaml_file", _yaml_files_to_run)
        else:
            metafunc.parametrize("yaml_file", [None])


def pytest_sessionstart(session):
    """
    pytest会话开始时的钩子函数
    """
    global _test_start_time
    _test_start_time = time.time()


def pytest_sessionfinish(session, exitstatus):
    """
    pytest会话结束时的钩子函数
    """
    # 注意：统计信息在test_yaml_case函数中累计
    # 这个钩子函数可以用来做额外的处理
    pass


# CI环境检测缓存
_ci_environment_cache = None

def _send_dingtalk_notification(final_stats: dict, test_duration: float):
    """
    发送钉钉通知（提取的公共函数）
    
    Args:
        final_stats: 最终统计信息
        test_duration: 测试执行时长
    """
    try:
        config = get_config()
        dingtalk_config = config.get_dingtalk_config()
        
        # 生成 Allure 报告链接
        report_url = None
        build_url = os.environ.get('BUILD_URL')
        if build_url:
            report_url = f"{build_url.rstrip('/')}/allure/"
        else:
            report_path = os.path.abspath('allure-report/index.html')
            if os.path.exists(report_path):
                report_url = f"本地报告路径: {report_path}"
        
        # 创建钉钉通知器
        dingtalk_notifier = DingTalkNotifier(
            webhook_url=dingtalk_config.get('webhook_url'),
            secret=dingtalk_config.get('secret'),
            at_mobiles=dingtalk_config.get('at_mobiles', []),
            at_all=dingtalk_config.get('at_all', False)
        )
        
        # 发送测试报告
        dingtalk_notifier.send_test_report(
            total=final_stats['total'],
            passed=final_stats['passed'],
            failed=final_stats['failed'],
            broken=final_stats.get('error', 0),
            skipped=final_stats['skipped'],
            duration=test_duration,
            report_url=report_url
        )
        print("✅ 钉钉通知已发送")
        logger.info("钉钉通知发送成功")
    except Exception as e:
        print(f"⚠️  发送钉钉通知失败: {e}")
        logger.error(f"发送钉钉通知失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()


def is_ci_environment():
    """
    检测是否在CI环境中运行（带缓存）
    
    Returns:
        bool: 如果在CI环境中返回True，否则返回False
    """
    global _ci_environment_cache
    
    # 如果已缓存，直接返回
    if _ci_environment_cache is not None:
        return _ci_environment_cache
    
    ci_env_vars = [
        'JENKINS_URL',      # Jenkins
        'CI',                # 通用CI标志
        'BUILD_NUMBER',      # Jenkins/GitLab CI
        'GITLAB_CI',         # GitLab CI
        'TRAVIS',            # Travis CI
        'CIRCLECI',          # CircleCI
        'GITHUB_ACTIONS',    # GitHub Actions
        'TEAMCITY_VERSION',  # TeamCity
        'GO_SERVER_URL',     # GoCD
    ]
    
    # 检查环境变量
    for var in ci_env_vars:
        if os.environ.get(var):
            _ci_environment_cache = True
            return True
    
    # 也可以通过配置强制启用（使用配置管理器，避免重复读取文件）
    try:
        config = get_config()
        dingtalk_config = config.get_dingtalk_config()
        if dingtalk_config.get('force_send_in_local', False):
            _ci_environment_cache = True
            return True
    except Exception:
        pass
    
    _ci_environment_cache = False
    return False


@allure.feature("接口自动化测试")
def test_yaml_case(yaml_file):
    """
    pytest测试函数，用于运行YAML测试用例
    
    Args:
        yaml_file: YAML测试用例文件路径
    """
    if yaml_file is None:
        pytest.skip("没有测试文件")
    
    # 打印文件信息，让用户知道正在执行哪个文件
    print(f"\n{SEPARATOR_LINE}")
    print(f"📁 正在执行测试文件: {yaml_file}")
    print(f"{SEPARATOR_LINE}\n")
    logger.info(f"开始执行测试文件: {yaml_file}")
    
    # 解析YAML文件，获取所有测试用例
    try:
        from parser.yaml_parser import YamlParser
        parser = YamlParser(yaml_file)
        test_cases = parser.parse()
        logger.info(f"成功解析 {len(test_cases)} 个测试用例")
    except Exception as e:
        logger.error(f"解析YAML文件失败: {e}", exc_info=True)
        raise TestFrameworkError(f"解析YAML文件失败: {e}", {'yaml_file': yaml_file})
    
    # 获取文件级前置登录配置
    file_pre_login = parser.get_file_pre_login()
    
    # 设置测试标题为YAML文件名（只设置一次，不在循环中设置）
    import os
    yaml_file_name = os.path.basename(yaml_file).replace('.yaml', '').replace('.yml', '')
    allure.dynamic.title(f"测试文件: {yaml_file_name}")
    allure.dynamic.suite(yaml_file_name)
    allure.dynamic.description(f"包含 {len(test_cases)} 个测试用例")
    
    # 为每个用例创建独立的测试
    runner = TestRunner()
    
    # 如果配置了文件级前置登录，先执行登录
    if file_pre_login:
        print(f"\n{'='*80}")
        print(f"🔑 执行文件级前置登录（文件: {yaml_file_name}）")
        print(f"{'='*80}\n")
        with allure.step(f"文件级前置登录: {yaml_file_name}"):
            try:
                runner._execute_pre_login(file_pre_login, f"{yaml_file_name}_文件级登录")
                print(f"✅ 文件级前置登录成功，该文件中的所有用例将使用此账号的token\n")
            except Exception as e:
                print(f"❌ 文件级前置登录失败: {e}\n")
                import traceback
                traceback.print_exc()
                raise
    total_cases = len(test_cases)
    passed_cases = 0
    failed_cases = 0
    error_cases = 0
    
    # 累计到全局统计并保存到文件
    global _test_stats
    stats_file = os.path.join(os.path.dirname(__file__), STATS_FILE)
    
    # 读取当前统计信息（从文件读取，确保跨进程/模块一致性）
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                file_stats = json.load(f)
                _test_stats['total'] = file_stats.get('total', 0)
                _test_stats['passed'] = file_stats.get('passed', 0)
                _test_stats['failed'] = file_stats.get('failed', 0)
                _test_stats['error'] = file_stats.get('error', 0)
                _test_stats['skipped'] = file_stats.get('skipped', 0)
        except Exception:
            pass  # 如果读取失败，使用内存中的值
    
    _test_stats['total'] += total_cases
    
    # 用于记录失败的用例信息，用于在Allure报告中显示
    failed_cases_info = []
    error_cases_info = []
    
    # 批量写入统计信息的计数器
    stats_write_counter = 0
    
    for index, test_case in enumerate(test_cases, 1):
        case_name = test_case.get('name', f'用例{index}')
        
        # 使用allure为每个用例创建独立的测试步骤
        step_title = f"执行用例: {case_name}"
        with allure.step(step_title):
            case_result = None  # 记录用例执行结果：'passed', 'failed', 'error'
            failure_message = None
            try:
                runner._run_test_case(test_case)
                passed_cases += 1
                _test_stats['passed'] += 1
                case_result = 'passed'
                print(f"✓ [{index}/{total_cases}] {case_name} - 执行成功")
                # 标记步骤为成功（在Allure中显示为绿色）
                allure.dynamic.severity(allure.severity_level.NORMAL)
            except AssertionError as e:
                failed_cases += 1
                _test_stats['failed'] += 1
                case_result = 'failed'
                failure_message = str(e)
                print(f"✗ [{index}/{total_cases}] {case_name} - 断言失败: {failure_message}")
                
                # 记录失败用例信息
                failed_cases_info.append({
                    'index': index,
                    'name': case_name,
                    'error': failure_message,
                    'type': '断言失败'
                })
                
                # 在Allure中标记失败，使用明显的标题
                allure.dynamic.severity(allure.severity_level.CRITICAL)
                # 附加详细的失败信息
                failure_detail = f"用例名称: {case_name}\n"
                failure_detail += f"失败原因: {failure_message}\n"
                failure_detail += f"用例序号: {index}/{total_cases}"
                allure.attach(failure_detail, f"❌ 用例失败详情: {case_name}", allure.attachment_type.TEXT)
                # 也附加原始错误信息
                allure.attach(str(e), "断言失败详情", allure.attachment_type.TEXT)
                # 标记测试失败
                allure.dynamic.label("test_status", "failed")
                allure.dynamic.label("failure_type", "assertion")
            except Exception as e:
                failed_cases += 1
                error_cases += 1
                _test_stats['error'] += 1
                case_result = 'error'
                failure_message = str(e)
                print(f"✗ [{index}/{total_cases}] {case_name} - 执行异常: {failure_message}")
                
                # 记录错误用例信息
                import traceback
                error_traceback = traceback.format_exc()
                error_cases_info.append({
                    'index': index,
                    'name': case_name,
                    'error': failure_message,
                    'traceback': error_traceback,
                    'type': '执行异常'
                })
                
                # 在Allure中标记错误，使用明显的标题
                allure.dynamic.severity(allure.severity_level.BLOCKER)
                # 附加详细的错误信息
                error_detail = f"用例名称: {case_name}\n"
                error_detail += f"错误信息: {failure_message}\n"
                error_detail += f"用例序号: {index}/{total_cases}\n\n"
                error_detail += f"异常堆栈:\n{error_traceback}"
                allure.attach(error_detail, f"⚠️ 用例执行异常: {case_name}", allure.attachment_type.TEXT)
                # 也附加原始错误信息
                allure.attach(str(e), "执行异常详情", allure.attachment_type.TEXT)
                allure.attach(error_traceback, "异常堆栈", allure.attachment_type.TEXT)
                traceback.print_exc()
                # 标记测试失败
                allure.dynamic.label("test_status", "error")
                allure.dynamic.label("failure_type", "exception")
            finally:
                # 批量写入统计信息（减少IO操作）
                stats_write_counter += 1
                should_write = (
                    stats_write_counter >= STATS_WRITE_INTERVAL or
                    case_result in ('failed', 'error') or
                    index == total_cases  # 最后一个用例
                )
                
                if should_write:
                    try:
                        with open(stats_file, 'w', encoding='utf-8') as f:
                            json.dump(_test_stats, f, ensure_ascii=False, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        stats_write_counter = 0
                    except Exception as save_error:
                        print(f"⚠️  保存统计信息失败: {save_error}")
            
            # 注意：不在循环中调用pytest.fail()，这样即使用例失败也会继续执行后续用例
            # 所有用例执行完成后，再统一判断是否失败
    
    # 最后再保存一次统计信息，确保所有数据都被写入
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(_test_stats, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as save_error:
        print(f"⚠️  最终保存统计信息失败: {save_error}")
    
    # 打印总结
    print(f"\n{SEPARATOR_LINE}")
    print(f"📊 测试文件执行总结: {yaml_file}")
    print(SEPARATOR_LINE)
    print(f"  总用例数: {total_cases}")
    print(f"  通过: {passed_cases}")
    print(f"  失败: {failed_cases}")
    print(f"{'='*80}\n")
    
    # 如果有失败的用例，在Allure报告中附加失败用例摘要
    if failed_cases_info or error_cases_info:
        failure_summary = SEPARATOR_LINE + "\n"
        failure_summary += "❌ 失败用例汇总\n"
        failure_summary += "=" * 80 + "\n\n"
        
        if failed_cases_info:
            failure_summary += f"【断言失败用例】共 {len(failed_cases_info)} 个:\n"
            failure_summary += "-" * 80 + "\n"
            for case_info in failed_cases_info:
                failure_summary += f"\n{case_info['index']}. {case_info['name']}\n"
                failure_summary += f"   错误: {case_info['error']}\n"
            failure_summary += "\n"
        
        if error_cases_info:
            failure_summary += f"【执行异常用例】共 {len(error_cases_info)} 个:\n"
            failure_summary += "-" * 80 + "\n"
            for case_info in error_cases_info:
                failure_summary += f"\n{case_info['index']}. {case_info['name']}\n"
                failure_summary += f"   错误: {case_info['error']}\n"
            failure_summary += "\n"
        
        failure_summary += SEPARATOR_LINE + "\n"
        failure_summary += f"总计: {len(failed_cases_info) + len(error_cases_info)} 个用例失败\n"
        failure_summary += SEPARATOR_LINE
        
        # 附加到Allure报告
        allure.attach(failure_summary, "❌ 失败用例汇总", allure.attachment_type.TEXT)
        
        # 如果有失败的用例，让pytest知道测试失败（在所有用例执行完成后）
        pytest.fail(f"{failed_cases + error_cases} 个用例执行失败（失败: {failed_cases}, 错误: {error_cases}）", pytrace=False)


if __name__ == '__main__':
    try:
        # 初始化配置管理器
        config = get_config()
        logger.info("配置管理器初始化成功")
        
        # 初始化日志系统（从配置读取）
        init_logger_from_config(config)
        logger.info("日志系统初始化成功")
        
    except ConfigError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
    
    # 重置测试统计信息（直接重置字典的值，保持引用一致）
    _test_stats['total'] = 0
    _test_stats['passed'] = 0
    _test_stats['failed'] = 0
    _test_stats['skipped'] = 0
    _test_stats['error'] = 0
    _test_start_time = time.time()
    
    # 清除之前的统计文件
    stats_file = os.path.join(os.path.dirname(__file__), STATS_FILE)
    if os.path.exists(stats_file):
        try:
            os.remove(stats_file)
        except Exception:
            pass
    
    # 设置Allure结果目录
    allure_results_dir = 'allure-results'
    
    # 清理旧的Allure结果（可选：保留最近N次的结果）
    import shutil
    if os.path.exists(allure_results_dir):
        # 删除旧的结果文件，每次运行前清理
        try:
            shutil.rmtree(allure_results_dir)
            print(f"🧹 已清理旧的Allure结果目录: {allure_results_dir}")
        except Exception as e:
            print(f"⚠️  清理Allure结果目录失败: {e}")
    
    # 创建新的结果目录
    os.makedirs(allure_results_dir, exist_ok=True)
    
    # 确定测试路径
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        # 默认运行tests目录下的测试用例
        test_path = os.path.join(
            os.path.dirname(__file__),
            'tests',
            'test_cases'
        )
        if not os.path.exists(test_path):
            print("未找到测试用例目录，请提供测试文件路径")
            print("用法: python main.py <yaml_file_or_directory>")
            sys.exit(1)
    
    # 获取所有YAML文件
    yaml_files = get_yaml_files(test_path)
    
    if not yaml_files:
        print(f"未找到YAML测试文件: {test_path}")
        sys.exit(1)
    
    print(f"找到 {len(yaml_files)} 个测试文件")
    
    # 设置要运行的YAML文件（供pytest使用）
    # 使用环境变量传递，因为pytest会在导入时就收集测试
    import os
    os.environ['YAML_TEST_FILES'] = ','.join(yaml_files)
    _yaml_files_to_run.extend(yaml_files)
    
    # 使用pytest运行测试，以便Allure能够正确收集结果
    print("\n开始运行测试...")
    pytest_args = [
        __file__,
        '-v',
        f'--alluredir={allure_results_dir}',
        '--tb=short',
        '-s',  # 不捕获输出，显示print和logging
        # 移除pytest的日志配置，使用我们自己的日志配置，避免重复
        # '--log-cli-level=INFO',
        # '--log-cli-format=%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # '--log-cli-date-format=%Y-%m-%d %H:%M:%S'
    ]
    
    exit_code = pytest.main(pytest_args)
    
    # 打印总体总结
    print(f"\n{SEPARATOR_LINE}")
    print(f"🎉 所有测试文件执行完成！")
    print(SEPARATOR_LINE)
    print(f"  共执行 {len(yaml_files)} 个测试文件")
    for yaml_file in yaml_files:
        print(f"    - {yaml_file}")
    print(f"{'='*80}\n")
    
    # 自动生成Allure报告
    print("\n正在生成Allure测试报告...")
    ReportGenerator.generate_allure_report()
    
    # 显示报告路径，不自动打开
    import os
    report_path = os.path.abspath('allure-report/index.html')
    print(f"✅ 测试报告已生成")
    print(f"📁 报告路径: {report_path}")
    print(f"💡 需要查看报告时，请手动打开上述路径")
    
    # 从文件读取最新的统计信息
    stats_file = os.path.join(os.path.dirname(__file__), STATS_FILE)
    final_stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'error': 0
    }
    
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                final_stats = json.load(f)
        except Exception as e:
            print(f"⚠️  读取统计信息失败: {e}")
            # 如果文件读取失败，尝试从模块中读取
            import sys
            current_module = sys.modules[__name__]
            final_stats = getattr(current_module, '_test_stats', final_stats)
    else:
        # 如果文件不存在，从模块中读取
        import sys
        current_module = sys.modules[__name__]
        final_stats = getattr(current_module, '_test_stats', final_stats)
    
    print(f"\n{'='*80}")
    print(f"📊 测试执行统计汇总")
    print(f"{'='*80}")
    print(f"  总用例数: {final_stats['total']}")
    print(f"  通过: {final_stats['passed']} ✅")
    print(f"  失败: {final_stats['failed']} ❌")
    print(f"  错误: {final_stats['error']} ⚠️")
    print(f"  跳过: {final_stats['skipped']} ⏭️")
    print(f"{SEPARATOR_LINE}\n")
    
    # 发送钉钉通知（仅在CI环境中发送）
    try:
        config = get_config()
        dingtalk_config = config.get_dingtalk_config()
        test_duration = time.time() - _test_start_time if _test_start_time else 0
        
        if is_ci_environment():
            print("检测到CI环境，正在发送钉钉通知...")
            logger.info("检测到CI环境，准备发送钉钉通知")
            _send_dingtalk_notification(final_stats, test_duration)
        elif dingtalk_config.get('force_send_in_local', False):
            print("检测到本地环境，但配置了强制发送，正在发送钉钉通知...")
            logger.info("本地环境，但配置了强制发送，准备发送钉钉通知")
            _send_dingtalk_notification(final_stats, test_duration)
        else:
            print("💡 本地环境，跳过钉钉通知（仅在CI环境中发送）")
            logger.info("本地环境，跳过钉钉通知")
    except ConfigError as e:
        logger.warning(f"获取钉钉配置失败，跳过通知: {e}")
    except Exception as e:
        logger.error(f"处理钉钉通知时发生错误: {e}", exc_info=True)
    
    # 清理统计文件
    if os.path.exists(stats_file):
        try:
            os.remove(stats_file)
        except Exception:
            pass
