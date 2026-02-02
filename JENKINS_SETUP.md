# Jenkins CI/CD 配置指南

本文档说明如何将接口自动化测试框架集成到 Jenkins 持续集成环境中。

## 📋 前置要求

### 1. Jenkins 环境要求

- Jenkins 2.x 或更高版本
- 已安装以下插件：
  - **Pipeline**（Jenkins Pipeline 插件）
  - **Allure Jenkins Plugin**（用于发布测试报告）
  - **Git Plugin**（用于代码检出）

### 2. 系统要求

- Python 3.7+ 已安装
- pip 已安装
- Allure 命令行工具（可选，如果使用 Allure 插件则不需要）

## 🚀 快速开始

### 步骤 1: 安装 Jenkins 插件

1. 登录 Jenkins 管理界面
2. 进入 **系统管理** -> **插件管理**
3. 安装以下插件：
   - **Allure Jenkins Plugin**
   - **Pipeline**
   - **Git Plugin**（如果未安装）

### 步骤 2: 配置 Jenkins Job

#### 方式一：使用 Pipeline（推荐）

1. 在 Jenkins 中创建新的 **Pipeline** 类型的 Job
2. 在 **Pipeline** 配置中：
   - **Definition**: 选择 "Pipeline script from SCM"
   - **SCM**: 选择 Git
   - **Repository URL**: 填写你的代码仓库地址
   - **Branch**: 填写分支名（如 `*/main` 或 `*/master`）
   - **Script Path**: 填写 `Jenkinsfile`

#### 方式二：使用自由风格项目

如果不想使用 Pipeline，可以手动配置各个构建步骤：

1. 创建 **自由风格的软件项目**
2. 配置 **源码管理**（Git）
3. 添加构建步骤：
   - **执行 shell**: 
     ```bash
     pip3 install -r requirements.txt
     python3 main.py tests/test_cases/
     ```
   - **Allure Report**（如果安装了 Allure 插件）:
     - Results path: `allure-results`

### 步骤 3: 配置钉钉通知

钉钉通知会在 CI 环境中**自动发送**，无需额外配置。框架会自动检测 `JENKINS_URL` 环境变量来判断是否在 CI 环境中。

确保在 `config/config.yaml` 中已配置钉钉 Webhook：

```yaml
dingtalk:
  webhook_url: "你的钉钉Webhook地址"
  secret: "你的密钥（如果使用了加签）"
  at_mobiles: []  # 可选
  at_all: false   # 可选
```

### 步骤 4: 运行构建

1. 点击 **立即构建**
2. 查看构建日志
3. 查看 Allure 测试报告（如果安装了 Allure 插件）

## 📊 Jenkinsfile 说明

### 主要阶段

1. **环境检查**: 检查 Python 和 pip 是否安装
2. **代码检出**: 从 Git 仓库检出代码
3. **安装依赖**: 安装 Python 依赖包
4. **安装 Allure**: 检查 Allure 工具是否可用
5. **运行测试**: 执行接口自动化测试
6. **生成测试报告**: 生成 Allure 测试报告
7. **发布测试报告**: 使用 Allure 插件发布报告

### 环境变量

Jenkinsfile 中使用的环境变量：

- `JENKINS_URL`: Jenkins 服务器地址（自动设置）
- `BUILD_NUMBER`: 构建编号（自动设置）
- `BUILD_URL`: 构建 URL（自动设置）
- `WORKSPACE`: 工作空间目录（自动设置）

### 构建状态

- **SUCCESS**: 所有测试通过
- **UNSTABLE**: 测试失败但继续执行（会生成报告）
- **FAILURE**: 构建过程出错

## 🔧 常见问题

### 1. Allure 报告无法生成

**问题**: 构建日志显示 "Allure 报告生成失败"

**解决方案**:
- 确保安装了 **Allure Jenkins Plugin**
- 或者在 Jenkins 服务器上安装 Allure 命令行工具
- 检查 `allure-results` 目录是否有测试结果文件

### 2. 钉钉通知未发送

**问题**: 测试完成后没有收到钉钉通知

**解决方案**:
- 检查 `config/config.yaml` 中的钉钉配置是否正确
- 确认 Jenkins 环境变量 `JENKINS_URL` 已设置
- 查看构建日志中是否有 "检测到CI环境" 的提示

### 3. Python 依赖安装失败

**问题**: pip install 失败

**解决方案**:
- 检查 Jenkins 服务器是否已安装 Python 3.7+
- 检查网络连接（可能需要配置代理）
- 尝试使用 `--trusted-host` 参数

### 4. 测试用例执行失败

**问题**: 测试用例执行失败但构建显示成功

**解决方案**:
- 检查测试用例的断言是否正确
- 检查 API 服务器是否可访问
- 查看 Allure 报告了解详细错误信息

## 📝 自定义配置

### 修改超时时间

在 Jenkinsfile 中修改：

```groovy
timeout(time: 60, unit: 'MINUTES')  // 改为60分钟
```

### 修改保留构建数量

在 Jenkinsfile 中修改：

```groovy
buildDiscarder(logRotator(numToKeepStr: '20'))  // 保留最近20次构建
```

### 运行指定测试用例

修改运行测试阶段：

```groovy
python3 main.py tests/test_cases/specific_test.yaml
```

## 🔗 相关链接

- [Jenkins Pipeline 文档](https://www.jenkins.io/doc/book/pipeline/)
- [Allure Jenkins Plugin](https://plugins.jenkins.io/allure-jenkins-plugin/)
- [项目 README](./README.md)

## 📞 支持

如有问题，请查看：
1. Jenkins 构建日志
2. Allure 测试报告
3. 项目 README 文档
