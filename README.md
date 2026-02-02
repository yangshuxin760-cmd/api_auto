> 一个基于Python的接口自动化测试框架，支持中文关键字驱动，让测试用例编写更简单、更直观。
## ✨ 特性

- 🎯 **中文关键字驱动** - 使用中文关键字编写测试用例，降低学习成本
- 📝 **YAML格式** - 使用YAML格式编写测试用例，简洁易读
- 🔐 **Token自动管理** - 自动提取和传递认证Token，无需手动处理
- 🔑 **前置登录支持** - 每个用例可配置独立的前置登录，自动注册和登录账号
- 🔗 **接口依赖支持** - 后续接口可引用前置接口的返回结果
- 🗄️ **SQL操作支持** - 支持前置SQL和后置SQL，SQL结果可作为接口参数
- ✅ **丰富的断言** - 支持状态码、字段值、字段不为空等多种断言方式
- 📊 **Allure报告** - 自动生成美观的Allure测试报告
- 📱 **钉钉通知** - 测试完成后自动发送钉钉群消息通知（CI环境自动发送）
- 🎲 **参数化测试** - 支持时间戳、随机数、UUID等动态参数
- 🏗️ **模块化设计** - 清晰的模块划分，易于扩展和维护

## 📦 项目结构

```
api_autuo2/
├── config/              # 配置文件
│   └── config.yaml      # 框架配置（API地址、数据库、Token等）
├── parser/              # YAML解析模块
│   └── yaml_parser.py   # 支持中文关键字转换
├── request/             # HTTP请求模块
│   └── http_client.py   # HTTP客户端，支持变量解析、Token管理
├── assertions/          # 断言模块
│   └── assertion.py     # 多种断言方法
├── database/            # 数据库模块
│   └── db_handler.py    # 数据库操作（前置/后置SQL）
├── runner/              # 测试运行器
│   └── test_runner.py   # 测试用例执行引擎
├── report/              # 报告生成模块
│   ├── report_generator.py  # Allure报告生成
│   └── dingtalk_notifier.py # 钉钉通知模块
├── tests/               # 测试用例
│   └── test_cases/      # YAML测试用例文件
├── main.py              # 主入口文件
└── requirements.txt     # 依赖包列表
```

## 🔔 钉钉通知配置

框架支持在测试执行完成后自动发送钉钉群消息通知。配置方法如下：

### 1. 获取钉钉机器人Webhook

1. 在钉钉群中点击"群设置" -> "智能群助手" -> "添加机器人"
2. 选择"自定义"机器人
3. 填写机器人名称，并设置安全设置（建议选择"加签"）
4. 复制Webhook地址和加签密钥

### 2. 配置文件设置

在 `config/config.yaml` 中配置钉钉通知：

```yaml
# 钉钉通知配置
dingtalk:
  # 钉钉机器人Webhook地址（必填）
  webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
  # 钉钉机器人密钥（可选，如果设置了加签，需要填写）
  secret: "YOUR_SECRET"
  # @的手机号列表（可选）
  at_mobiles: []
  # 是否@所有人（可选，默认false）
  at_all: false
```

### 3. 环境变量配置（可选）

也可以通过环境变量配置：

```bash
export DINGTALK_WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
export DINGTALK_SECRET="YOUR_SECRET"
export DINGTALK_AT_MOBILES="13800138000,13900139000"
export DINGTALK_AT_ALL="false"
```

### 4. 通知内容

钉钉通知消息包含：
- ✅ 测试执行状态（全部通过/测试失败）
- 📊 测试统计（总用例数、通过数、失败数、中断数、跳过数）
- 📈 通过率
- ⏱️ 执行时长

配置完成后，每次测试执行完成都会自动发送钉钉通知！
