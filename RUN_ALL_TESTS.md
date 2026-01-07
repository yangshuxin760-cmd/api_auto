# 运行所有测试用例

## 方法1：运行整个测试目录（推荐）

直接运行测试目录，会自动发现并执行目录下所有的 YAML 测试文件：

```bash
python main.py tests/test_cases/
```

或者不传参数，使用默认路径：

```bash
python main.py
```

## 方法2：运行单个测试文件

运行指定的测试文件：

```bash
# 运行注册接口测试
python main.py tests/test_cases/register_test_complete.yaml

# 运行登录接口测试
python main.py tests/test_cases/login_test.yaml
```

## 方法3：运行多个指定文件

可以指定多个文件（用空格分隔）：

```bash
python main.py tests/test_cases/register_test_complete.yaml tests/test_cases/login_test.yaml
```

## 运行结果

运行所有用例时，会显示：

```
找到 2 个测试文件

开始运行测试...
✓ [1/10] 用户注册_正常场景 - 执行成功
✓ [2/10] 用户注册_用户名已存在 - 执行成功
...
✓ [10/10] 用户登录_正常场景 - 执行成功

测试执行总结:
  总用例数: 10
  通过: 10
  失败: 0
============================================================
```

## 查看测试报告

测试完成后会自动生成 Allure 报告，程序会询问是否在浏览器中打开：

```
正在生成Allure测试报告...
Allure报告已生成: allure-report/index.html

是否在浏览器中打开Allure报告? (y/n):
```

输入 `y` 会自动打开浏览器查看报告。

## 手动查看报告

```bash
# 生成报告
allure generate allure-results -o allure-report --clean

# 打开报告
allure open allure-report
```

## 当前测试文件

当前 `tests/test_cases/` 目录下的测试文件：

- `register_test_complete.yaml` - 用户注册接口完整测试用例
- `login_test.yaml` - 用户登录接口测试用例

## 注意事项

1. **用例依赖**：某些用例可能依赖其他用例的执行结果（如登录用例依赖注册用例），框架会自动处理依赖关系
2. **执行顺序**：用例按照 YAML 文件中的顺序执行
3. **失败处理**：即使某个用例失败，也会继续执行后续用例
4. **报告生成**：所有用例执行完成后会生成统一的 Allure 报告

## 快速命令

```bash
# 运行所有用例（最常用）
python main.py

# 运行所有用例并自动打开报告
python main.py && allure open allure-report

# 只运行注册测试
python main.py tests/test_cases/register_test_complete.yaml

# 只运行登录测试
python main.py tests/test_cases/login_test.yaml
```

