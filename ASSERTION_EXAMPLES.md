# 断言使用示例

## 断言字段的三种方式

### 1. 断言字段不为空

```yaml
断言:
  字段断言:
    - 字段: id
      不为空: true
```

**说明**：验证字段存在且不为空（不是null、空字符串、空列表或空字典）

### 2. 断言字段等于期望值

```yaml
断言:
  字段断言:
    - 字段: detail
      期望值: Email already exists
```

**说明**：验证字段的值完全等于指定的期望值

### 3. 断言字段等于请求参数

```yaml
断言:
  字段断言:
    - 字段: username
      期望值: ${request.json.username}
```

**说明**：验证响应字段的值等于请求参数中的值（常用于验证返回的数据与请求一致）

## 完整示例

### 示例1：验证错误消息

```yaml
- 用例名称: 用户注册_邮箱已存在
  请求方法: POST
  请求地址: /register
  请求体:
    username: new_user_${timestamp}
    email: existing@test.com
    password: testpass123
  断言:
    状态码: 400
    字段断言:
      - 字段: detail
        期望值: Email already exists
```

### 示例2：验证用户名重复错误

```yaml
- 用例名称: 用户注册_用户名已存在
  请求方法: POST
  请求地址: /register
  请求体:
    username: existing_user
    email: new_email_${timestamp}@test.com
    password: testpass123
  断言:
    状态码: 400
    字段断言:
      - 字段: detail
        期望值: Username already exists
```

### 示例3：验证成功返回的数据

```yaml
- 用例名称: 用户注册_正常场景
  请求方法: POST
  请求地址: /register
  请求体:
    username: autotest_${timestamp}
    email: autotest_${timestamp}@test.com
    password: testpass123
  断言:
    状态码: 200
    字段断言:
      - 字段: id
        不为空: true
      - 字段: username
        期望值: ${request.json.username}
      - 字段: email
        期望值: ${request.json.email}
```

### 示例4：验证嵌套字段

```yaml
断言:
  字段断言:
    - 字段: data.user.id
      不为空: true
    - 字段: data.user.name
      期望值: testuser
    - 字段: data.code
      期望值: 0
```

## 常见错误消息断言

### 邮箱相关错误

```yaml
- 字段: detail
  期望值: Email already exists
```

### 用户名相关错误

```yaml
- 字段: detail
  期望值: Username already exists
```

### 验证错误

```yaml
- 字段: detail
  不为空: true  # 验证错误信息存在，但不关心具体内容
```

## 注意事项

1. **字符串匹配**：期望值必须完全匹配，区分大小写
2. **类型匹配**：期望值的类型必须与响应字段类型一致
3. **嵌套字段**：使用点号（.）访问嵌套字段，如 `data.user.id`
4. **数组字段**：使用索引访问数组元素，如 `data.items.0.name`

## 断言优先级

如果同时指定了 `不为空` 和 `期望值`：
- 优先执行 `期望值` 断言
- `不为空` 断言会在 `期望值` 断言之后执行

## 错误提示

当断言失败时，会显示详细的错误信息：
```
字段 detail 断言失败: 期望 Email already exists, 实际 Username already exists
```

