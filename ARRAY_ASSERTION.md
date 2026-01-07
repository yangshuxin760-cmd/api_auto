# 数组字段断言说明

## 支持数组索引访问

框架支持通过索引访问数组中的元素，格式为：`字段名.索引.子字段`

## 使用示例

### 示例1：断言 detail 数组中的 msg

当响应结构为：
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "username"],
      "msg": "Field required"
    }
  ]
}
```

可以这样断言：

```yaml
断言:
  字段断言:
    - 字段: detail.0.msg
      期望值: Field required
    - 字段: detail.0.type
      期望值: missing
    - 字段: detail.0.loc.0
      期望值: body
    - 字段: detail.0.loc.1
      期望值: username
```

### 示例2：访问嵌套数组

如果响应结构为：
```json
{
  "errors": [
    {
      "messages": [
        "错误1",
        "错误2"
      ]
    }
  ]
}
```

可以这样断言：

```yaml
断言:
  字段断言:
    - 字段: errors.0.messages.0
      期望值: 错误1
    - 字段: errors.0.messages.1
      期望值: 错误2
```

### 示例3：完整用例示例

```yaml
- 用例名称: 用户登录_缺少用户名
  请求方法: POST
  请求地址: /login
  请求体:
    password: testpass123
  断言:
    状态码: 422
    字段断言:
      - 字段: detail.0.msg
        期望值: Field required
      - 字段: detail.0.loc.0
        期望值: body
      - 字段: detail.0.loc.1
        期望值: username
      - 字段: detail.0.type
        期望值: missing
```

## 字段路径说明

### 基本格式
- `字段名` - 访问对象字段
- `字段名.索引` - 访问数组元素（索引从0开始）
- `字段名.索引.子字段` - 访问数组元素中的字段
- `字段名.字段名.索引` - 访问嵌套结构

### 路径示例

| 路径 | 说明 | 示例值 |
|------|------|--------|
| `detail.0` | detail数组的第一个元素 | `{"type": "missing", ...}` |
| `detail.0.msg` | detail数组第一个元素的msg字段 | `"Field required"` |
| `detail.0.loc.0` | detail数组第一个元素的loc数组的第一个元素 | `"body"` |
| `detail.0.loc.1` | detail数组第一个元素的loc数组的第二个元素 | `"username"` |
| `data.items.0.id` | data对象的items数组第一个元素的id字段 | `123` |

## 常见使用场景

### 场景1：验证错误消息

```yaml
断言:
  字段断言:
    - 字段: detail.0.msg
      期望值: Field required
```

### 场景2：验证错误位置

```yaml
断言:
  字段断言:
    - 字段: detail.0.loc.0
      期望值: body
    - 字段: detail.0.loc.1
      期望值: username
```

### 场景3：验证错误类型

```yaml
断言:
  字段断言:
    - 字段: detail.0.type
      期望值: missing
```

### 场景4：验证多个错误

如果响应包含多个错误：

```json
{
  "detail": [
    {"msg": "错误1"},
    {"msg": "错误2"}
  ]
}
```

可以这样断言：

```yaml
断言:
  字段断言:
    - 字段: detail.0.msg
      期望值: 错误1
    - 字段: detail.1.msg
      期望值: 错误2
```

## 注意事项

1. **索引从0开始**：数组索引从0开始，第一个元素是 `0`，第二个是 `1`
2. **索引必须是数字**：路径中的数字会被识别为数组索引
3. **嵌套支持**：支持多层嵌套，如 `detail.0.loc.1`
4. **错误提示**：如果路径不存在，会显示详细的错误信息

## 完整示例

```yaml
- 用例名称: 验证错误响应
  请求方法: POST
  请求地址: /api/endpoint
  请求体:
    field1: value1
  断言:
    状态码: 422
    字段断言:
      - 字段: detail.0.type
        期望值: missing
      - 字段: detail.0.msg
        期望值: Field required
      - 字段: detail.0.loc.0
        期望值: body
      - 字段: detail.0.loc.1
        期望值: field2
```

