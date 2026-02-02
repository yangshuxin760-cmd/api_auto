pipeline {
    agent any
    
    environment {
        // Python 版本（根据你的 Jenkins 环境调整）
        PYTHON_VERSION = '3.9'
        // 项目目录
        PROJECT_DIR = "${WORKSPACE}"
        // 测试结果目录
        ALLURE_RESULTS = "${WORKSPACE}/allure-results"
        ALLURE_REPORT = "${WORKSPACE}/allure-report"
    }
    
    options {
        // 保留最近10次构建
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // 超时设置（30分钟）
        timeout(time: 30, unit: 'MINUTES')
        // 添加时间戳
        timestamps()
    }
    
    stages {
        stage('环境检查') {
            steps {
                script {
                    echo "=========================================="
                    echo "检查 Python 环境"
                    echo "=========================================="
                    sh 'python3 --version || python --version'
                    sh 'pip3 --version || pip --version'
                }
            }
        }
        
        stage('代码检出') {
            steps {
                script {
                    echo "=========================================="
                    echo "检出代码"
                    echo "=========================================="
                    checkout scm
                }
            }
        }
        
        stage('安装依赖') {
            steps {
                script {
                    echo "=========================================="
                    echo "安装 Python 依赖"
                    echo "=========================================="
                    sh '''
                        # 升级 pip
                        python3 -m pip install --upgrade pip --quiet || python -m pip install --upgrade pip --quiet
                        
                        # 安装项目依赖
                        pip3 install -r requirements.txt --quiet || pip install -r requirements.txt --quiet
                        
                        # 验证关键依赖是否安装成功
                        python3 -c "import requests, yaml, pytest, allure" || python -c "import requests, yaml, pytest, allure"
                        echo "✅ 依赖安装成功"
                    '''
                }
            }
        }
        
        stage('安装 Allure') {
            steps {
                script {
                    echo "=========================================="
                    echo "检查 Allure 命令行工具"
                    echo "=========================================="
                    sh '''
                        if ! command -v allure &> /dev/null; then
                            echo "Allure 未安装，尝试安装..."
                            # 如果 Jenkins 有 Allure 插件，可以跳过这一步
                            # 或者使用以下命令安装（需要根据系统调整）
                            # wget https://github.com/allure-framework/allure2/releases/download/2.24.0/allure-2.24.0.tgz
                            # tar -xzf allure-2.24.0.tgz
                            # export PATH=$PATH:$(pwd)/allure-2.24.0/bin
                            echo "请确保 Jenkins 已安装 Allure 插件或系统已安装 Allure 命令行工具"
                        else
                            echo "Allure 已安装: $(allure --version)"
                        fi
                    '''
                }
            }
        }
        
        stage('运行测试') {
            steps {
                script {
                    echo "=========================================="
                    echo "运行接口自动化测试"
                    echo "=========================================="
                    // 设置 Jenkins 环境变量（确保钉钉通知能正确识别CI环境）
                    env.JENKINS_URL = env.JENKINS_URL ?: 'http://localhost:8080'
                    
                    // 运行测试（即使失败也继续执行后续步骤）
                    def testResult = sh(
                        script: '''
                            cd ${PROJECT_DIR}
                            # 运行所有测试用例
                            python3 main.py tests/test_cases/ || python main.py tests/test_cases/
                        ''',
                        returnStatus: true  // 返回退出码，不中断流程
                    )
                    
                    // 检查测试结果
                    sh '''
                        if [ -d "${ALLURE_RESULTS}" ]; then
                            echo "测试结果已生成: ${ALLURE_RESULTS}"
                            RESULT_COUNT=$(find ${ALLURE_RESULTS} -name "*.json" 2>/dev/null | wc -l)
                            echo "找到 ${RESULT_COUNT} 个测试结果文件"
                            ls -la ${ALLURE_RESULTS} | head -20
                        else
                            echo "警告: 未找到测试结果目录"
                        fi
                    '''
                    
                    // 根据测试结果设置构建状态
                    if (testResult != 0) {
                        echo "⚠️ 测试执行失败，退出码: ${testResult}"
                        currentBuild.result = 'UNSTABLE'
                    } else {
                        echo "✅ 测试执行成功"
                    }
                }
            }
        }
        
        stage('生成测试报告') {
            steps {
                script {
                    echo "=========================================="
                    echo "生成 Allure 测试报告"
                    echo "=========================================="
                    sh '''
                        cd ${PROJECT_DIR}
                        if [ -d "${ALLURE_RESULTS}" ] && [ "$(ls -A ${ALLURE_RESULTS})" ]; then
                            allure generate ${ALLURE_RESULTS} -o ${ALLURE_REPORT} --clean || echo "Allure 报告生成失败，可能未安装 Allure 命令行工具"
                        else
                            echo "警告: 测试结果目录为空，跳过报告生成"
                        fi
                    '''
                }
            }
        }
        
        stage('发布测试报告') {
            steps {
                script {
                    echo "=========================================="
                    echo "发布 Allure 测试报告"
                    echo "=========================================="
                    // 使用 Allure 插件发布报告（需要安装 Allure Jenkins Plugin）
                    // 如果插件未安装，这一步会失败但不影响整体流程
                    try {
                        allure([
                            includeProperties: false,
                            jdk: '',
                            properties: [],
                            reportBuildPolicy: 'ALWAYS',
                            results: [[path: 'allure-results']]
                        ])
                        echo "Allure 报告已成功发布"
                    } catch (Exception e) {
                        echo "警告: Allure 插件未安装或配置有误，跳过报告发布"
                        echo "错误信息: ${e.getMessage()}"
                        echo "请安装 Allure Jenkins Plugin: https://plugins.jenkins.io/allure-jenkins-plugin/"
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "=========================================="
                echo "清理临时文件"
                echo "=========================================="
                // 清理 Python 缓存和临时文件
                sh '''
                    find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
                    find . -type f -name "*.pyc" -delete 2>/dev/null || true
                    find . -type f -name ".test_stats.json" -delete 2>/dev/null || true
                    echo "✅ 清理完成"
                '''
            }
        }
        
        success {
            script {
                echo "=========================================="
                echo "✅ 测试执行成功！"
                echo "=========================================="
                // 钉钉通知会在 main.py 中自动发送（CI 环境检测）
            }
        }
        
        failure {
            script {
                echo "=========================================="
                echo "❌ 测试执行失败！"
                echo "=========================================="
                // 钉钉通知会在 main.py 中自动发送（CI 环境检测）
            }
        }
        
        unstable {
            script {
                echo "=========================================="
                echo "⚠️ 测试执行不稳定！"
                echo "=========================================="
            }
        }
    }
}
