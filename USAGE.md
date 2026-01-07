# 框架使用说明

## 快速开始

### 1. 运行单个测试文件

```bash
python main.py tests/test_cases/register_test_complete.yaml
```

### 2. 运行整个测试目录

```bash
python main.py tests/test_cases/
```

### 3. 运行结果

测试执行完成后会显示：
- ✓ 测试文件执行完成（成功）
- ✗ 测试文件执行失败（失败，会显示错误信息）

## 测试用例编写

### 基本格式（中文关键字）

```yaml
- 用例名称: 用户注册接口测试
  用例描述: 测试用户注册功能
  请求方法: POST
  请求地址: /register
  请求头:
    Content-Type: application/json
  请求体:
    username: testuser_001
    email: testuser_001@example.com
    password: testpass123
  断言:
    状态码: 200
    字段断言:
      - 字段: id
        不为空: true
      - 字段: username
        期望值: testuser_001
    响应不为空: true
```

## 运行示例

### 成功示例

```
找到 1 个测试文件

正在运行: tests/test_cases/register_test_complete.yaml
✓ tests/test_cases/register_test_complete.yaml 执行完成

正在生成Allure测试报告...
Allure报告已生成: allure-report/index.html
```

### 失败示例

```
找到 1 个测试文件

正在运行: tests/test_cases/register_test_complete.yaml
用例执行失败: 用户注册接口测试
错误信息: 状态码断言失败: 期望 200, 实际 400
✗ tests/test_cases/register_test_complete.yaml 执行失败
```

## 查看测试报告

### 自动生成

测试运行完成后会自动生成Allure报告，程序会询问是否在浏览器中打开。

### 手动查看

```bash
# 生成报告
allure generate allure-results -o allure-report --clean

# 打开报告（浏览器）
allure open allure-report
```

## 注意事项

1. **唯一性要求**：如果API有唯一性约束（如用户名、邮箱），请使用唯一的值，避免重复注册导致测试失败
2. **网络连接**：确保能够访问配置的API地址
3. **Allure工具**：如需查看HTML报告，需要安装Allure命令行工具

## 常见问题

### Q: 测试返回400错误？
A: 可能是请求参数不符合API要求，或存在唯一性约束冲突。检查响应内容中的错误信息。

### Q: 如何查看详细的请求和响应？
A: 查看Allure报告，报告中包含完整的请求头、请求体、响应内容等信息。

### Q: 如何调试测试用例？
A: 
1. 查看控制台输出的错误信息
2. 查看Allure报告中的详细步骤
3. 使用curl或Postman先验证API是否正常

