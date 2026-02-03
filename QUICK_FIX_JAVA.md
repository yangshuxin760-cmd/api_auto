# 快速修复 Java 环境问题

## 问题

构建日志显示：`Unable to locate a Java Runtime`

## 解决方案

### 步骤 1: 创建 Java 系统链接

在终端执行以下命令（需要输入密码）：

```bash
sudo ln -sfn /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk
```

### 步骤 2: 验证 Java 安装

```bash
# 验证 Java 是否可用
/opt/homebrew/opt/openjdk@11/bin/java -version
```

应该显示：
```
openjdk version "11.0.30" ...
```

### 步骤 3: 提交并推送 Jenkinsfile 更新

我已经在 Jenkinsfile 中添加了 Java 环境变量配置，需要提交并推送：

```bash
git add Jenkinsfile
git commit -m "添加 Java 环境变量配置"
git push origin main
```

### 步骤 4: 重新运行构建

在 Jenkins 中重新运行构建，Allure 报告应该可以正常生成了。

## 如果仍然有问题

如果创建系统链接后仍然有问题，可以在 Jenkins 系统配置中手动配置 Java：

1. 进入 **Manage Jenkins** -> **Tools**
2. 找到 **JDK** 部分
3. 点击 **Add JDK**
4. 填写：
   - **Name**: `JDK-11`
   - **JAVA_HOME**: `/opt/homebrew/opt/openjdk@11`
5. 保存

然后在 Jenkinsfile 的 `allure()` 步骤中指定 JDK：

```groovy
allure([
    jdk: 'JDK-11',  // 使用配置的 JDK
    // ... 其他配置
])
```
