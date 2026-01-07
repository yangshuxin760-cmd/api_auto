"""
报告生成模块
支持Allure测试报告生成
"""
import subprocess
import os
import sys
from typing import List


class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_allure_report(
        results_dir: str = 'allure-results',
        report_dir: str = 'allure-report'
    ):
        """
        生成Allure测试报告
        
        Args:
            results_dir: Allure结果目录
            report_dir: Allure报告目录
        """
        # 确保结果目录存在
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # 生成报告
        try:
            subprocess.run(
                ['allure', 'generate', results_dir, '-o', report_dir, '--clean'],
                check=True,
                capture_output=True
            )
            print(f"Allure报告已生成: {report_dir}/index.html")
        except subprocess.CalledProcessError as e:
            print(f"生成Allure报告失败: {e}")
            print("请确保已安装Allure命令行工具")
        except FileNotFoundError:
            print("未找到Allure命令行工具，请先安装Allure")
            print("安装方法: https://docs.qameta.io/allure/")
    
    @staticmethod
    def open_allure_report(report_dir: str = 'allure-report'):
        """
        打开Allure报告（在浏览器中）
        
        Args:
            report_dir: Allure报告目录
        """
        try:
            subprocess.run(
                ['allure', 'open', report_dir],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"打开Allure报告失败: {e}")
        except FileNotFoundError:
            print("未找到Allure命令行工具")

