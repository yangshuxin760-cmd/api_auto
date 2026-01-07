# 快速开始指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 安装Allure命令行工具

### macOS
```bash
brew install allure
```

### Linux
```bash
# 下载并安装Allure
wget https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.tgz
tar -zxvf allure-2.24.1.tgz
sudo mv allure-2.24.1 /opt/allure
sudo ln -s /opt/allure/bin/allure /usr/local/bin/allure
```

### Windows
1. 下载Allure: https://github.com/allure-framework/allure2/releases
2. 解压并添加到系统PATH

## 3. 配置

编辑 `config/config.yaml`:

```yaml
base_url: http://your-api-server.com  # 修改为你的API服务器地址
timeout: 30

database:
  host: localhost
  port: 3306
  user: your_user
  password: your_password
  database: your_database
  charset: utf8mb4

token:
  field_path: data.token        # Token在响应中的路径
  header_key: Authorization      # Token请求头名称
  prefix: Bearer                 # Token前缀
```

## 4. 编写测试用例

在 `tests/test_cases/` 目录下创建YAML测试用例文件。

参考 `tests/test_cases/example.yaml` 查看示例。

## 5. 运行测试

```bash
# 运行单个测试文件
python main.py tests/test_cases/example.yaml

# 运行整个测试目录
python main.py tests/test_cases/
```

## 6. 查看报告

测试运行完成后，会自动生成Allure报告。

手动生成报告：
```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```

## 测试用例编写示例（中文关键字驱动）

框架支持**中文关键字驱动**，所有关键字都可以使用中文，更符合中文使用习惯。

### 基础用例

```yaml
- 用例名称: 获取用户列表
  用例描述: 测试获取用户列表接口
  请求方法: GET
  请求地址: /api/users
  请求头:
    Content-Type: application/json
  断言:
    状态码: 200
    字段断言:
      - 字段: data
        不为空: true
```

### 带Token自动传递

```yaml
- 用例名称: 用户登录
  请求方法: POST
  请求地址: /api/login
  请求体:
    username: admin
    password: 123456
  断言:
    状态码: 200
    字段断言:
      - 字段: data.token
        不为空: true

# 后续接口会自动使用登录获取的token
- 用例名称: 获取个人信息
  请求方法: GET
  请求地址: /api/user/info
  断言:
    状态码: 200
```

### 接口依赖

```yaml
- 用例名称: 创建订单
  请求方法: POST
  请求地址: /api/orders
  请求体:
    product_id: 123
  断言:
    状态码: 200
    字段断言:
      - 字段: data.order_id
        不为空: true

# 引用前置接口的返回结果
- 用例名称: 取消订单
  请求方法: POST
  请求地址: /api/orders/cancel
  请求体:
    order_id: ${创建订单.data.order_id}  # 引用创建订单接口返回的order_id
  断言:
    状态码: 200
```

### SQL操作

```yaml
- 用例名称: 创建订单（带SQL）
  前置SQL: SELECT id, price FROM products WHERE id = 1
  请求方法: POST
  请求地址: /api/orders
  请求体:
    product_id: ${sql.id}      # 引用SQL查询结果的id字段
    quantity: 2
    total_price: ${sql.price}  # 引用SQL查询结果的price字段
  断言:
    状态码: 200
  后置SQL: UPDATE orders SET status = 'completed' WHERE id = LAST_INSERT_ID()
```

### 完整示例（用户注册）

```yaml
- 用例名称: 用户注册接口测试
  用例描述: 测试用户注册功能，验证注册接口是否正常工作
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
      - 字段: email
        期望值: testuser_001@example.com
      - 字段: created_at
        不为空: true
    响应不为空: true
```

### 关键字对照表

| 中文关键字 | 英文关键字（兼容） | 说明 |
|-----------|------------------|------|
| 用例名称 | name | 测试用例名称 |
| 用例描述 | description | 测试用例描述 |
| 请求方法 | method | HTTP请求方法 |
| 请求地址 | url | 接口路径 |
| 请求头 | headers | HTTP请求头 |
| 请求参数 | params | URL查询参数 |
| 请求体 | json | JSON格式请求体 |
| 表单数据 | data | Form表单数据 |
| 前置SQL | pre_sql | 执行接口前执行的SQL |
| 后置SQL | post_sql | 执行接口后执行的SQL |
| 断言 | assertions | 断言配置 |
| 状态码 | status_code | 期望的HTTP状态码 |
| 字段断言 | fields | 字段断言列表 |
| 字段 | field | 要断言的字段路径 |
| 不为空 | not_empty | 断言字段不为空 |
| 期望值 | expected_value | 字段的期望值 |
| 响应不为空 | not_empty | 断言整个响应不为空 |

**注意**: 框架同时支持中文和英文关键字，可以混合使用。

## 常见问题

### 1. Token未自动传递
- 检查 `config/config.yaml` 中的 `token.field_path` 是否正确
- 确认登录接口返回的token路径与配置一致

### 2. 接口依赖引用失败
- 确保用例名称与引用时使用的名称完全一致（包括中文）
- 确保被引用的用例在当前用例之前执行

### 3. SQL执行失败
- 检查数据库配置是否正确
- 确认数据库连接信息无误
- 检查SQL语句语法是否正确

### 4. Allure报告未生成
- 确认已安装Allure命令行工具
- 检查 `allure-results` 目录是否存在
- 查看错误日志

