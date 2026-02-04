# 测试用例编写指南

## 📋 目录

1. [框架概述](#框架概述)
2. [YAML文件格式](#yaml文件格式)
3. [关键词说明](#关键词说明)
4. [变量引用](#变量引用)
5. [前置登录配置](#前置登录配置)
6. [SQL操作](#sql操作)
7. [断言方式](#断言方式)
8. [完整示例](#完整示例)

---

## 框架概述

本框架支持**中文关键字驱动**的YAML格式测试用例，让测试用例编写更简单、更直观。

### 特点

- ✅ 使用中文关键字，降低学习成本
- ✅ 支持接口依赖，后续接口可引用前置接口的返回结果
- ✅ 自动Token管理，登录后自动提取和传递token
- ✅ 支持前置登录，每个用例可配置独立账号
- ✅ 支持SQL操作，前置/后置SQL，SQL结果可作为接口参数
- ✅ 丰富的断言方式，支持状态码、字段值、字段不为空等

---

## YAML文件格式

### 格式1：用例列表格式（推荐）

```yaml
# 文件级前置登录配置（可选）
前置登录:
  自动注册: true
  用户名: user_${timestamp}
  密码: testpass123
  邮箱: user_${timestamp}@test.com

# 用例列表
用例列表:
  - 用例名称: 用例1
    请求方法: GET
    请求地址: /api/users
    
  - 用例名称: 用例2
    请求方法: POST
    请求地址: /api/users
```

### 格式2：纯用例列表格式

```yaml
- 用例名称: 用例1
  请求方法: GET
  请求地址: /api/users

- 用例名称: 用例2
  请求方法: POST
  请求地址: /api/users
```

### 格式3：单个用例格式

```yaml
用例名称: 单个用例
请求方法: GET
请求地址: /api/users
```

---

## 关键词说明

### 1. 用例基本信息

#### `用例名称` (必填)
- **说明**: 测试用例的名称，用于标识用例和接口依赖引用
- **类型**: 字符串
- **示例**:
  ```yaml
  用例名称: 用户登录_正常场景
  ```

#### `用例描述` (可选)
- **说明**: 用例的描述信息（已废弃，保留兼容）
- **类型**: 字符串
- **示例**:
  ```yaml
  用例描述: 测试用户正常登录场景
  ```

---

### 2. 请求相关关键词

#### `请求方法`
- **说明**: HTTP请求方法
- **类型**: 字符串
- **可选值**: `GET`, `POST`, `PUT`, `DELETE`, `PATCH` 等
- **默认值**: `GET`
- **示例**:
  ```yaml
  请求方法: POST
  ```

#### `请求地址`
- **说明**: API接口路径（相对路径或完整URL）
- **类型**: 字符串
- **支持**: 变量引用 `${用例名称.字段}` 或 `${timestamp}` 等
- **示例**:
  ```yaml
  请求地址: /api/users
  请求地址: /users/${用户注册.id}  # 使用变量引用
  ```

#### `请求头`
- **说明**: HTTP请求头
- **类型**: 字典
- **示例**:
  ```yaml
  请求头:
    Content-Type: application/json
    X-Custom-Header: value
  ```

#### `请求参数`
- **说明**: URL查询参数（GET请求常用）
- **类型**: 字典
- **示例**:
  ```yaml
  请求参数:
    page: 1
    size: 10
    keyword: ${timestamp}  # 支持变量引用
  ```

#### `请求体`
- **说明**: JSON格式的请求体（POST/PUT请求常用）
- **类型**: 字典
- **示例**:
  ```yaml
  请求体:
    username: test_user
    email: test@example.com
    password: testpass123
  ```

#### `表单数据`
- **说明**: 表单格式的请求体
- **类型**: 字典或字符串
- **示例**:
  ```yaml
  表单数据:
    field1: value1
    field2: value2
  ```

---

### 3. Token控制

#### `不使用token`
- **说明**: 是否禁用token（用于测试未登录场景）
- **类型**: 布尔值
- **默认值**: `false`（默认使用token）
- **示例**:
  ```yaml
  不使用token: true  # 不发送token，用于权限校验测试
  ```

**注意**: 
- 如果配置了前置登录，默认会自动使用登录获取的token
- 设置 `不使用token: true` 后，即使有token也不会发送

---

### 4. 前置登录配置

#### `前置登录`
- **说明**: 用例级前置登录配置，为当前用例获取独立的登录token
- **类型**: 字典
- **优先级**: 用例级 > 文件级 > 全局token
- **示例**:
  ```yaml
  前置登录:
    自动注册: true
    用户名: user_${timestamp}
    密码: testpass123
    邮箱: user_${timestamp}@test.com
    注册接口: /register
    登录接口: /login
    登录方法: POST
  ```

#### 前置登录子关键词

| 关键词 | 说明 | 类型 | 必填 | 默认值 |
|--------|------|------|------|--------|
| `自动注册` | 是否自动注册账号 | 布尔值 | 否 | `false` |
| `用户名` | 登录用户名 | 字符串 | 是 | - |
| `密码` | 登录密码 | 字符串 | 是 | - |
| `邮箱` | 注册邮箱（自动注册时必填） | 字符串 | 否 | - |
| `注册接口` | 注册接口路径 | 字符串 | 否 | `/register` |
| `登录接口` | 登录接口路径 | 字符串 | 否 | `/login` |
| `登录方法` | 登录请求方法 | 字符串 | 否 | `POST` |
| `登录请求体` | 自定义登录请求体 | 字典 | 否 | - |

**完整示例**:
```yaml
- 用例名称: 需要独立账号的用例
  前置登录:
    自动注册: true
    用户名: test_user_${timestamp}
    密码: testpass123
    邮箱: test_user_${timestamp}@test.com
  请求方法: POST
  请求地址: /api/posts
  请求体:
    title: "测试文章"
```

---

### 5. SQL操作

#### `前置SQL`
- **说明**: 执行用例前执行的SQL语句，结果可作为接口参数
- **类型**: 字符串
- **示例**:
  ```yaml
  前置SQL: SELECT id FROM users WHERE username = 'test' LIMIT 1
  ```

**SQL结果引用**:
```yaml
请求体:
  user_id: ${sql.id}  # 引用SQL查询结果的id字段
```

#### `后置SQL`
- **说明**: 执行用例后执行的SQL语句（用于清理数据等）
- **类型**: 字符串
- **示例**:
  ```yaml
  后置SQL: DELETE FROM test_data WHERE id = ${sql.id}
  ```

---

### 6. 断言相关关键词

#### `断言`
- **说明**: 断言配置块
- **类型**: 字典
- **示例**:
  ```yaml
  断言:
    状态码: 200
    字段断言:
      - 字段: id
        不为空: true
    响应不为空: true
  ```

#### `状态码`
- **说明**: 期望的HTTP状态码
- **类型**: 整数
- **示例**:
  ```yaml
  断言:
    状态码: 200
  ```

#### `字段断言`
- **说明**: 字段断言列表
- **类型**: 列表
- **示例**:
  ```yaml
  断言:
    字段断言:
      - 字段: id
        不为空: true
      - 字段: username
        期望值: test_user
      - 字段: email
        期望值: ${request.json.email}  # 引用请求参数
  ```

#### `字段`
- **说明**: 要断言的字段路径（支持嵌套，用点号分隔）
- **类型**: 字符串
- **示例**:
  ```yaml
  字段: id                    # 一级字段
  字段: data.user.name        # 嵌套字段
  字段: items.0.title         # 数组字段（索引从0开始）
  字段: detail.0.msg          # 嵌套数组字段
  ```

#### `期望值`
- **说明**: 字段的期望值
- **类型**: 任意类型（字符串、数字、布尔值等）
- **支持**: 变量引用 `${用例名称.字段}` 或 `${request.json.字段}`
- **示例**:
  ```yaml
  字段断言:
    - 字段: username
      期望值: test_user
    - 字段: id
      期望值: ${用户注册.id}  # 引用前置用例的响应
    - 字段: email
      期望值: ${request.json.email}  # 引用当前请求参数
  ```

#### `不为空`
- **说明**: 断言字段不为空
- **类型**: 布尔值
- **示例**:
  ```yaml
  字段断言:
    - 字段: id
      不为空: true
  ```

#### `响应不为空`
- **说明**: 断言整个响应不为空
- **类型**: 布尔值
- **示例**:
  ```yaml
  断言:
    响应不为空: true
  ```

---

## 变量引用

### 1. 内置变量

框架提供以下内置变量：

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `${timestamp}` | 当前时间戳（秒） | `1704067200` |
| `${timestamp_ms}` | 当前时间戳（毫秒） | `1704067200000` |
| `${random}` | 随机整数（0-999999） | `123456` |
| `${random_int}` | 随机整数（0-999999） | `789012` |
| `${uuid}` | UUID | `550e8400-e29b-41d4-a716-446655440000` |
| `${uuid_short}` | 短UUID（无横线） | `550e8400e29b41d4a716446655440000` |

**使用示例**:
```yaml
请求体:
  username: test_user_${timestamp}
  email: test_${random}@example.com
  order_id: ${uuid}
```

### 2. 接口依赖变量

引用前置用例的响应数据：

**格式**: `${用例名称.字段路径}`

**示例**:
```yaml
# 用例1：注册用户
- 用例名称: 用户注册
  请求方法: POST
  请求地址: /register
  请求体:
    username: test_user
    email: test@example.com
  断言:
    状态码: 200

# 用例2：使用注册返回的用户ID
- 用例名称: 获取用户详情
  请求方法: GET
  请求地址: /users/${用户注册.id}  # 引用注册接口返回的id
  断言:
    状态码: 200
    字段断言:
      - 字段: id
        期望值: ${用户注册.id}  # 在断言中也可以引用
      - 字段: username
        期望值: ${用户注册.username}
```

**嵌套字段引用**:
```yaml
# 如果响应是: {"data": {"user": {"id": 123}}}
请求地址: /users/${用例名称.data.user.id}
```

**数组字段引用**:
```yaml
# 如果响应是: {"items": [{"id": 1}, {"id": 2}]}
请求地址: /items/${用例名称.items.0.id}  # 引用第一个元素的id
```

### 3. 请求参数引用

在断言中引用当前请求的参数：

**格式**: `${request.json.字段}` 或 `${request.params.字段}`

**示例**:
```yaml
- 用例名称: 创建用户
  请求方法: POST
  请求地址: /users
  请求体:
    username: test_user
    email: test@example.com
  断言:
    状态码: 200
    字段断言:
      - 字段: username
        期望值: ${request.json.username}  # 引用请求体中的username
      - 字段: email
        期望值: ${request.json.email}      # 引用请求体中的email
```

**支持的请求类型**:
- `${request.json.字段}` - 引用JSON请求体
- `${request.data.字段}` - 引用表单数据
- `${request.params.字段}` - 引用URL参数
- `${request.headers.字段}` - 引用请求头

### 4. 字符串中嵌入变量

支持在字符串中嵌入变量：

**示例**:
```yaml
请求体:
  username: test_user_${timestamp}  # 结果: test_user_1704067200
  email: user_${random}@test.com   # 结果: user_123456@test.com
```

---

## 前置登录配置

### 文件级前置登录

在YAML文件开头配置，该文件中的所有用例都使用同一个账号：

```yaml
# 文件级前置登录配置
前置登录:
  自动注册: true
  用户名: file_user_${timestamp}
  密码: testpass123
  邮箱: file_user_${timestamp}@test.com

用例列表:
  - 用例名称: 用例1
    请求方法: GET
    请求地址: /api/users
    # 自动使用文件级登录的token
    
  - 用例名称: 用例2
    请求方法: POST
    请求地址: /api/posts
    # 自动使用文件级登录的token
```

### 用例级前置登录

为单个用例配置独立的前置登录：

```yaml
- 用例名称: 需要独立账号的用例
  前置登录:
    自动注册: true
    用户名: case_user_${timestamp}
    密码: testpass123
    邮箱: case_user_${timestamp}@test.com
  请求方法: POST
  请求地址: /api/posts
```

**优先级**: 用例级 > 文件级 > 全局token

---

## SQL操作

### 前置SQL

执行用例前执行SQL，结果可作为接口参数：

```yaml
- 用例名称: 使用SQL数据的用例
  前置SQL: SELECT id, name FROM users WHERE status = 'active' LIMIT 1
  请求方法: POST
  请求地址: /api/orders
  请求体:
    user_id: ${sql.id}      # 引用SQL查询结果的id字段
    user_name: ${sql.name}  # 引用SQL查询结果的name字段
  断言:
    状态码: 200
```

### 后置SQL

执行用例后执行SQL（用于清理数据）：

```yaml
- 用例名称: 创建测试数据
  请求方法: POST
  请求地址: /api/test_data
  请求体:
    name: test_data
  后置SQL: DELETE FROM test_data WHERE name = 'test_data'
  断言:
    状态码: 200
```

**注意**: 
- SQL结果以字典形式存储，字段名作为key
- 如果查询返回多行，只使用第一行
- SQL结果引用格式：`${sql.字段名}`

---

## 断言方式

### 1. 状态码断言

```yaml
断言:
  状态码: 200
```

### 2. 字段值断言

```yaml
断言:
  字段断言:
    - 字段: id
      期望值: 123
    - 字段: username
      期望值: test_user
```

### 3. 字段不为空断言

```yaml
断言:
  字段断言:
    - 字段: id
      不为空: true
    - 字段: token
      不为空: true
```

### 4. 嵌套字段断言

```yaml
断言:
  字段断言:
    - 字段: data.user.id
      期望值: 123
    - 字段: data.user.name
      期望值: test_user
```

### 5. 数组字段断言

```yaml
断言:
  字段断言:
    - 字段: items.0.id      # 第一个元素的id
      期望值: 1
    - 字段: items.0.name    # 第一个元素的name
      期望值: item1
    - 字段: items.1.id      # 第二个元素的id
      期望值: 2
```

### 6. 响应不为空断言

```yaml
断言:
  响应不为空: true
```

### 7. 组合断言

```yaml
断言:
  状态码: 200
  字段断言:
    - 字段: id
      不为空: true
    - 字段: username
      期望值: ${request.json.username}
    - 字段: email
      期望值: ${request.json.email}
  响应不为空: true
```

---

## 完整示例

### 示例1：用户注册和登录流程

```yaml
# 用例1：注册用户
- 用例名称: 用户注册
  请求方法: POST
  请求地址: /register
  请求头:
    Content-Type: application/json
  请求体:
    username: test_user_${timestamp}
    email: test_${timestamp}@example.com
    password: testpass123
  断言:
    状态码: 200
    字段断言:
      - 字段: id
        不为空: true
      - 字段: username
        期望值: ${request.json.username}
    响应不为空: true

# 用例2：登录获取token
- 用例名称: 用户登录
  请求方法: POST
  请求地址: /login
  请求头:
    Content-Type: application/json
  请求体:
    username: ${用户注册.username}
    password: testpass123
  断言:
    状态码: 200
    字段断言:
      - 字段: access_token
        不为空: true
      - 字段: token_type
        期望值: bearer

# 用例3：使用token访问需要认证的接口
- 用例名称: 获取用户信息
  请求方法: GET
  请求地址: /users/${用户注册.id}
  请求头:
    Content-Type: application/json
  # token会自动从登录接口获取并添加到请求头
  断言:
    状态码: 200
    字段断言:
      - 字段: id
        期望值: ${用户注册.id}
      - 字段: username
        期望值: ${用户注册.username}
```

### 示例2：使用文件级前置登录

```yaml
# 文件级前置登录配置
前置登录:
  自动注册: true
  用户名: file_user_${timestamp}
  密码: testpass123
  邮箱: file_user_${timestamp}@test.com

用例列表:
  # 用例1：自动使用文件级登录的token
  - 用例名称: 创建文章
    请求方法: POST
    请求地址: /posts
    请求头:
      Content-Type: application/json
    请求体:
      title: "测试文章"
      content: "这是测试内容"
    断言:
      状态码: 200
      字段断言:
        - 字段: id
          不为空: true

  # 用例2：同样使用文件级登录的token
  - 用例名称: 获取文章列表
    请求方法: GET
    请求地址: /posts
    断言:
      状态码: 200
      响应不为空: true
```

### 示例3：权限校验测试

```yaml
# 用例1：注册并登录
- 用例名称: 用户注册并登录
  前置登录:
    自动注册: true
    用户名: auth_user_${timestamp}
    密码: testpass123
    邮箱: auth_user_${timestamp}@test.com
  请求方法: POST
  请求地址: /login
  请求体:
    username: auth_user_${timestamp}
    password: testpass123
  断言:
    状态码: 200

# 用例2：未登录访问（权限校验）
- 用例名称: 未登录访问_权限校验
  请求方法: GET
  请求地址: /users/1
  不使用token: true  # 关键：不发送token
  请求头:
    Content-Type: application/json
  断言:
    状态码: 403  # 期望返回403未授权
    字段断言:
      - 字段: detail
        不为空: true
```

### 示例4：使用SQL操作

```yaml
# 用例1：使用前置SQL获取数据
- 用例名称: 使用SQL数据创建订单
  前置SQL: SELECT id, name FROM users WHERE role = 'customer' LIMIT 1
  请求方法: POST
  请求地址: /orders
  请求头:
    Content-Type: application/json
  请求体:
    user_id: ${sql.id}      # 使用SQL查询结果的id
    user_name: ${sql.name} # 使用SQL查询结果的name
    product: "测试商品"
  断言:
    状态码: 200
    字段断言:
      - 字段: order_id
        不为空: true
  后置SQL: DELETE FROM orders WHERE user_id = ${sql.id}  # 清理测试数据
```

---

## 关键词速查表

| 中文关键词 | 英文关键词 | 说明 | 必填 |
|-----------|-----------|------|------|
| `用例名称` | `name` | 用例名称 | ✅ |
| `请求方法` | `method` | HTTP方法 | ❌ |
| `请求地址` | `url` | API路径 | ✅ |
| `请求头` | `headers` | 请求头 | ❌ |
| `请求参数` | `params` | URL参数 | ❌ |
| `请求体` | `json` | JSON请求体 | ❌ |
| `表单数据` | `data` | 表单数据 | ❌ |
| `不使用token` | `no_token` | 禁用token | ❌ |
| `前置登录` | `pre_login` | 前置登录配置 | ❌ |
| `前置SQL` | `pre_sql` | 前置SQL | ❌ |
| `后置SQL` | `post_sql` | 后置SQL | ❌ |
| `断言` | `assertions` | 断言配置 | ❌ |
| `状态码` | `status_code` | 期望状态码 | ❌ |
| `字段断言` | `fields` | 字段断言列表 | ❌ |
| `字段` | `field` | 字段路径 | ❌ |
| `期望值` | `expected_value` | 期望值 | ❌ |
| `不为空` | `not_empty` | 不为空断言 | ❌ |
| `响应不为空` | `not_empty` | 响应不为空 | ❌ |

---

## 注意事项

1. **用例名称唯一性**: 用例名称用于接口依赖引用，建议使用唯一且有意义的名称
2. **变量引用顺序**: 用例按顺序执行，只能引用前置用例的响应
3. **Token自动管理**: 登录后token会自动提取和传递，无需手动处理
4. **文件级登录**: 文件级前置登录会在所有用例执行前执行一次
5. **SQL结果**: SQL查询结果以字典形式存储，只使用第一行数据
6. **字段路径**: 嵌套字段用点号分隔，数组索引从0开始

---

## 常见问题

### Q: 如何引用前置用例的响应数据？
A: 使用 `${用例名称.字段路径}` 格式，例如：`${用户注册.id}`

### Q: 如何禁用token？
A: 设置 `不使用token: true`

### Q: 如何为每个用例使用不同的账号？
A: 使用用例级 `前置登录` 配置

### Q: 如何在断言中引用请求参数？
A: 使用 `${request.json.字段}` 格式

### Q: 如何引用SQL查询结果？
A: 使用 `${sql.字段名}` 格式

---

## 更多示例

查看 `tests/test_cases/` 目录下的示例文件：
- `login_test.yaml` - 登录相关测试
- `get_user_list.yaml` - 用户详情接口测试
- `post_user.yaml` - 文章创建测试
- `register_test_complete.yaml` - 注册接口完整测试
