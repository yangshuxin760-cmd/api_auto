> 一个基于Python的接口自动化测试框架，支持中文关键字驱动，让测试用例编写更简单、更直观。
## ✨ 特性

- 🎯 **中文关键字驱动** - 使用中文关键字编写测试用例，降低学习成本
- 📝 **YAML格式** - 使用YAML格式编写测试用例，简洁易读
- 🔐 **Token自动管理** - 自动提取和传递认证Token，无需手动处理
- 🔗 **接口依赖支持** - 后续接口可引用前置接口的返回结果
- 🗄️ **SQL操作支持** - 支持前置SQL和后置SQL，SQL结果可作为接口参数
- ✅ **丰富的断言** - 支持状态码、字段值、字段不为空等多种断言方式
- 📊 **Allure报告** - 自动生成美观的Allure测试报告
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
│   └── report_generator.py  # Allure报告生成
├── tests/               # 测试用例
│   └── test_cases/      # YAML测试用例文件
├── main.py              # 主入口文件
└── requirements.txt     # 依赖包列表
```
