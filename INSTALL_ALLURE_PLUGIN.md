# 安装 Allure Jenkins Plugin 指南

本指南将帮助你在 Jenkins 中安装 Allure Jenkins Plugin，以便直接在 Jenkins 构建页面查看测试报告。

## 📦 安装步骤

### 步骤 1: 进入插件管理

1. 登录 Jenkins Web 界面
2. 点击左侧菜单的 **Manage Jenkins**（管理 Jenkins）
3. 点击 **Manage Plugins**（管理插件）

### 步骤 2: 搜索并安装插件

1. 切换到 **Available**（可用插件）标签页
2. 在搜索框中输入：`Allure Jenkins Plugin`
3. 找到 **Allure Jenkins Plugin** 插件
4. 勾选插件名称前的复选框
5. 点击页面底部的 **Install without restart**（不重启安装）或 **Download now and install after restart**（下载并在重启后安装）

### 步骤 3: 等待安装完成

- 安装过程可能需要几分钟
- 页面会显示安装进度
- 安装完成后会显示 "Success" 或 "Successfully installed"

### 步骤 4: 重启 Jenkins（如果需要）

- 如果选择了 "Install without restart"，插件会立即生效
- 如果选择了 "Download now and install after restart"，需要重启 Jenkins：
  ```bash
  # 在终端执行
  brew services restart jenkins-lts
  ```

## ✅ 验证安装

### 方法 1: 检查插件列表

1. 进入 **Manage Jenkins** -> **Manage Plugins**
2. 切换到 **Installed**（已安装）标签页
3. 搜索 "Allure"
4. 确认 **Allure Jenkins Plugin** 显示为已安装

### 方法 2: 运行构建测试

1. 在 Jenkins 中运行你的 Pipeline Job
2. 构建完成后，查看构建页面
3. 如果插件安装成功，左侧菜单应该会显示 **Allure Report** 链接
4. 点击链接即可查看测试报告

## 🔧 配置说明

安装插件后，Jenkinsfile 中的 `allure()` 步骤会自动工作，无需额外配置。

### Jenkinsfile 中的配置

```groovy
allure([
    includeProperties: false,
    jdk: '',
    properties: [],
    reportBuildPolicy: 'ALWAYS',
    results: [[path: 'allure-results']]
])
```

这个配置会：
- 从 `allure-results` 目录读取测试结果
- 自动生成并发布 Allure 报告
- 在构建页面显示报告链接

## 📊 查看报告

安装插件后，每次构建完成后：

1. 进入构建详情页面
2. 在左侧菜单中找到 **Allure Report** 链接
3. 点击链接打开 Allure 测试报告
4. 报告包含：
   - 测试概览（总用例数、通过率等）
   - 测试用例详情
   - 失败用例的错误信息
   - 测试执行时间线
   - 图表和统计信息

## 🐛 常见问题

### 1. 插件安装失败

**问题**: 插件下载超时或安装失败

**解决方案**:
- 检查网络连接
- 尝试使用 Jenkins 更新中心镜像
- 手动下载插件并上传安装

### 2. 构建页面没有 Allure Report 链接

**问题**: 插件已安装，但构建页面没有显示报告链接

**解决方案**:
- 确认 `allure-results` 目录中有测试结果文件
- 检查 Jenkinsfile 中的 `allure()` 步骤是否正确执行
- 查看构建日志，确认是否有错误信息
- 重启 Jenkins 服务

### 3. 报告显示为空

**问题**: 点击 Allure Report 链接，但报告内容为空

**解决方案**:
- 确认测试执行时使用了 `--alluredir=allure-results` 参数
- 检查 `allure-results` 目录中是否有 `.json` 文件
- 确认测试用例确实执行了（查看构建日志）

## 📚 相关资源

- [Allure Jenkins Plugin 官方文档](https://plugins.jenkins.io/allure-jenkins-plugin/)
- [Allure Framework 文档](https://docs.qameta.io/allure/)
- [项目 README](./README.md)

## 💡 提示

- 插件安装后，所有使用 `allure-results` 目录的构建都会自动生成报告
- 报告会保留在构建历史中，可以随时查看
- 如果不需要报告，可以在 Jenkinsfile 中注释掉 `allure()` 步骤
