# 变量参数化功能说明

## 功能概述

框架支持在YAML测试用例中使用变量参数化，每次运行测试时自动生成唯一的值，避免重复数据导致测试失败。

## 支持的内置变量

### 时间戳变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `${timestamp}` | 当前时间戳（秒） | `1767697994` |
| `${timestamp_ms}` | 当前时间戳（毫秒） | `1767697994123` |

### 随机数变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `${random}` | 随机整数（0-999999） | `400532` |
| `${random_int}` | 随机整数（0-999999） | `123456` |

### UUID变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `${uuid}` | 标准UUID | `22b91ecc-a21f-4d46-8309-15b55863c032` |
| `${uuid_short}` | 短UUID（无横线） | `22b91ecca21f4d46830915b55863c032` |

## 使用方式

### 方式1：直接使用变量

```yaml
请求体:
  username: autotest_${timestamp}
  email: autotest_${timestamp}@test.com
```

运行时会自动替换为：
```json
{
  "username": "autotest_1767697994",
  "email": "autotest_1767697994@test.com"
}
```

### 方式2：在字符串中嵌入变量

```yaml
请求体:
  username: user_${timestamp}_${random}
  email: test_${uuid_short}@example.com
```

运行时会自动替换为：
```json
{
  "username": "user_1767697994_400532",
  "email": "test_22b91ecca21f4d46830915b55863c032@example.com"
}
```

## 使用示例

### 示例1：用户注册（使用时间戳）

```yaml
- 用例名称: 用户注册接口测试
  请求方法: POST
  请求地址: /register
  请求体:
    username: autotest_${timestamp}
    email: autotest_${timestamp}@test.com
    password: testpass123
  断言:
    状态码: 200
```

**优势**：每次运行都会生成唯一的用户名和邮箱，避免重复注册错误。

### 示例2：创建订单（使用随机数）

```yaml
- 用例名称: 创建订单
  请求方法: POST
  请求地址: /api/orders
  请求体:
    order_no: ORDER_${random}
    user_id: ${random_int}
  断言:
    状态码: 200
```

### 示例3：混合使用多个变量

```yaml
- 用例名称: 创建用户
  请求方法: POST
  请求地址: /api/users
  请求体:
    username: user_${timestamp}
    email: ${uuid_short}@test.com
    code: CODE_${random}
  断言:
    状态码: 200
```

## 变量替换时机

变量替换在发送HTTP请求之前进行，具体流程：

1. **YAML解析**：解析YAML文件，保留变量字符串
2. **变量解析**：在发送请求前，解析所有 `${variable}` 格式的变量
3. **请求发送**：使用解析后的值发送HTTP请求

## 断言中引用请求参数

在断言中可以使用 `${request.json.field}` 格式引用请求参数，验证响应中的值是否与请求中的值一致。

### 使用示例

```yaml
请求体:
  username: autotest_${timestamp}
  email: autotest_${timestamp}@test.com

断言:
  字段断言:
    - 字段: username
      期望值: ${request.json.username}  # 验证响应username等于请求username
    - 字段: email
      期望值: ${request.json.email}     # 验证响应email等于请求email
```

### 支持的请求参数类型

- `${request.json.field}` - 引用JSON请求体中的字段
- `${request.data.field}` - 引用Form表单数据中的字段
- `${request.params.field}` - 引用URL参数中的字段
- `${request.headers.field}` - 引用请求头中的字段

### 完整示例

```yaml
- 用例名称: 用户注册接口测试
  请求方法: POST
  请求地址: /register
  请求体:
    username: autotest_${timestamp}
    email: autotest_${timestamp}@test.com
    password: testpass123
  断言:
    状态码: 200
    字段断言:
      - 字段: username
        期望值: ${request.json.username}  # 验证返回的username与请求一致
      - 字段: email
        期望值: ${request.json.email}     # 验证返回的email与请求一致
      - 字段: id
        不为空: true
```

## 与其他变量的兼容性

框架支持多种变量类型，按优先级解析：

1. **内置变量**：`${timestamp}`, `${random}`, `${uuid}` 等
2. **SQL结果变量**：`${sql.field}` - 引用前置SQL查询结果
3. **接口依赖变量**：`${用例名称.field}` - 引用前置接口响应
4. **请求参数变量**：`${request.json.field}` - 在断言中引用请求参数（仅用于断言）

### 组合使用示例

```yaml
- 用例名称: 登录
  请求方法: POST
  请求地址: /api/login
  请求体:
    username: user_${timestamp}
    password: test123
  断言:
    状态码: 200

- 用例名称: 获取用户信息
  请求方法: GET
  请求地址: /api/user/info
  请求头:
    Authorization: Bearer ${登录.data.token}
  断言:
    状态码: 200
```

## 注意事项

1. **变量格式**：必须使用 `${variable}` 格式，大括号内不能有空格
2. **字符串嵌入**：可以在字符串中嵌入变量，如 `prefix_${timestamp}_suffix`
3. **唯一性保证**：使用 `${timestamp}` 可以保证每次运行的值都不同
4. **随机性**：`${random}` 每次运行都会生成不同的随机数
5. **大小写敏感**：变量名区分大小写，如 `${timestamp}` 正确，`${Timestamp}` 错误

## 常见使用场景

### 场景1：避免重复注册

```yaml
请求体:
  username: testuser_${timestamp}
  email: test_${timestamp}@example.com
```

### 场景2：生成唯一订单号

```yaml
请求体:
  order_no: ORDER_${timestamp}_${random}
```

### 场景3：创建唯一标识

```yaml
请求体:
  code: CODE_${uuid_short}
  reference_id: REF_${random}
```

## 调试技巧

如果变量没有正确替换，可以：

1. 查看日志输出：框架会打印实际的请求参数
2. 检查变量格式：确保使用 `${variable}` 格式
3. 验证变量名：确保变量名拼写正确

## 扩展变量

如需添加自定义变量，可以修改 `request/http_client.py` 中的 `_resolve_builtin_variables` 方法。

