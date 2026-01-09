"""
主入口文件
可以直接执行测试
"""
import os
import sys
import pytest
import allure
from runner.test_runner import TestRunner
from report.report_generator import ReportGenerator


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
    print(f"\n{'='*80}")
    print(f"📁 正在执行测试文件: {yaml_file}")
    print(f"{'='*80}\n")
    
    # 解析YAML文件，获取所有测试用例
    from parser.yaml_parser import YamlParser
    parser = YamlParser(yaml_file)
    test_cases = parser.parse()
    
    # 设置测试标题为YAML文件名（只设置一次，不在循环中设置）
    import os
    yaml_file_name = os.path.basename(yaml_file).replace('.yaml', '').replace('.yml', '')
    allure.dynamic.title(f"测试文件: {yaml_file_name}")
    allure.dynamic.suite(yaml_file_name)
    allure.dynamic.description(f"包含 {len(test_cases)} 个测试用例")
    
    # 为每个用例创建独立的测试
    runner = TestRunner()
    total_cases = len(test_cases)
    passed_cases = 0
    failed_cases = 0
    
    for index, test_case in enumerate(test_cases, 1):
        case_name = test_case.get('name', f'用例{index}')
        case_description = test_case.get('description', '')
        
        # 使用allure为每个用例创建独立的测试步骤
        with allure.step(f"执行用例: {case_name}"):
            try:
                runner._run_test_case(test_case)
                passed_cases += 1
                print(f"✓ [{index}/{total_cases}] {case_name} - 执行成功")
            except AssertionError as e:
                failed_cases += 1
                print(f"✗ [{index}/{total_cases}] {case_name} - 断言失败: {str(e)}")
                # 继续执行，不中断
                allure.attach(str(e), "断言失败", allure.attachment_type.TEXT)
                # 标记测试失败
                allure.dynamic.label("test_status", "failed")
                pytest.fail(f"断言失败: {str(e)}", pytrace=False)
            except Exception as e:
                failed_cases += 1
                print(f"✗ [{index}/{total_cases}] {case_name} - 执行异常: {str(e)}")
                allure.attach(str(e), "执行异常", allure.attachment_type.TEXT)
                import traceback
                traceback.print_exc()
                # 标记测试失败
                allure.dynamic.label("test_status", "error")
                pytest.fail(f"执行异常: {str(e)}", pytrace=False)
    
    # 打印总结
    print(f"\n{'='*80}")
    print(f"📊 测试文件执行总结: {yaml_file}")
    print(f"{'='*80}")
    print(f"  总用例数: {total_cases}")
    print(f"  通过: {passed_cases}")
    print(f"  失败: {failed_cases}")
    print(f"{'='*80}\n")
    
    # 如果有失败的用例，让pytest知道测试失败
    if failed_cases > 0:
        pytest.fail(f"{failed_cases} 个用例执行失败")


if __name__ == '__main__':
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
    print(f"\n{'='*80}")
    print(f"🎉 所有测试文件执行完成！")
    print(f"{'='*80}")
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
