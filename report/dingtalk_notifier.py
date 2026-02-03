"""
钉钉通知模块
支持发送测试结果报告到钉钉群
"""
import json
import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import yaml


class DingTalkNotifier:
    """钉钉通知器"""
    
    def __init__(self, webhook_url: str = None, secret: str = None, 
                 at_mobiles: list = None, at_all: bool = False, config_path: str = None):
        """
        初始化钉钉通知器
        
        Args:
            webhook_url: 钉钉Webhook地址（优先使用）
            secret: 钉钉密钥（优先使用）
            at_mobiles: @的手机号列表（优先使用）
            at_all: 是否@所有人（优先使用）
            config_path: 配置文件路径（已废弃，保留以兼容旧代码）
        """
        # 如果直接提供了参数，优先使用参数
        if webhook_url or secret is not None or at_mobiles is not None or at_all:
            self.webhook_url = webhook_url
            self.secret = secret
            self.at_mobiles = at_mobiles or []
            self.at_all = at_all
        else:
            # 否则从配置管理器加载
            self._load_config_from_manager()
    
    def _load_config_from_manager(self):
        """从配置管理器加载钉钉配置"""
        try:
            from config.config_manager import get_config
            config = get_config()
            dingtalk_config = config.get_dingtalk_config()
            self.webhook_url = dingtalk_config.get('webhook_url')
            self.secret = dingtalk_config.get('secret')
            self.at_mobiles = dingtalk_config.get('at_mobiles', [])
            self.at_all = dingtalk_config.get('at_all', False)
        except Exception as e:
            print(f"⚠️  加载钉钉配置失败: {e}")
            self.webhook_url = None
            self.secret = None
            self.at_mobiles = []
            self.at_all = False
        else:
            # 尝试从环境变量获取
            self.webhook_url = os.environ.get('DINGTALK_WEBHOOK_URL')
            self.secret = os.environ.get('DINGTALK_SECRET')
            at_mobiles_str = os.environ.get('DINGTALK_AT_MOBILES', '')
            if at_mobiles_str:
                self.at_mobiles = [m.strip() for m in at_mobiles_str.split(',')]
            self.at_all = os.environ.get('DINGTALK_AT_ALL', 'false').lower() == 'true'
    
    def _get_sign(self, timestamp: int) -> str:
        """
        生成钉钉签名（如果配置了secret）
        
        Args:
            timestamp: 时间戳
            
        Returns:
            签名字符串
        """
        if not self.secret:
            return ''
        
        import hmac
        import hashlib
        import base64
        from urllib.parse import quote_plus
        
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def _get_webhook_url(self) -> Optional[str]:
        """
        获取完整的webhook URL（包含签名）
        
        Returns:
            完整的webhook URL
        """
        if not self.webhook_url:
            return None
        
        if not self.secret:
            return self.webhook_url
        
        import time
        timestamp = int(round(time.time() * 1000))
        sign = self._get_sign(timestamp)
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
    
    def _get_at_users(self) -> str:
        """
        获取@用户列表
        
        Returns:
            @用户的Markdown字符串
        """
        at_text = ""
        if self.at_all:
            at_text = "@所有人 "
        if self.at_mobiles:
            for mobile in self.at_mobiles:
                at_text += f"@{mobile} "
        return at_text.strip()
    
    def _parse_allure_results(self, results_dir: str = 'allure-results') -> Dict[str, Any]:
        """
        解析Allure结果文件，获取测试统计信息
        
        Args:
            results_dir: Allure结果目录
            
        Returns:
            测试统计信息字典
        """
        stats = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'broken': 0,
            'skipped': 0,
            'unknown': 0
        }
        
        if not os.path.exists(results_dir):
            return stats
        
        # 遍历所有测试用例结果文件
        for filename in os.listdir(results_dir):
            if filename.startswith('') and filename.endswith('.json'):
                filepath = os.path.join(results_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        status = data.get('status', 'unknown')
                        stats['total'] += 1
                        if status == 'passed':
                            stats['passed'] += 1
                        elif status == 'failed':
                            stats['failed'] += 1
                        elif status == 'broken':
                            stats['broken'] += 1
                        elif status == 'skipped':
                            stats['skipped'] += 1
                        else:
                            stats['unknown'] += 1
                except Exception as e:
                    print(f"⚠️  解析Allure结果文件失败 {filename}: {e}")
        
        return stats
    
    def send_test_report(
        self,
        total: int = 0,
        passed: int = 0,
        failed: int = 0,
        broken: int = 0,
        skipped: int = 0,
        duration: float = 0,
        report_url: str = None
    ) -> bool:
        """
        发送测试报告到钉钉
        
        Args:
            total: 总用例数
            passed: 通过数
            failed: 失败数
            broken: 中断数
            skipped: 跳过数
            duration: 执行时长（秒）
            report_url: 报告链接地址
            
        Returns:
            是否发送成功
        """
        if not self.webhook_url:
            print("⚠️  钉钉webhook未配置，跳过钉钉通知")
            return False
        
        # 计算通过率
        passed_rate = (passed / total * 100) if total > 0 else 0
        
        # 确定消息状态和颜色
        if failed == 0 and broken == 0:
            status = "✅ 全部通过"
            status_color = "green"
        elif failed > 0 or broken > 0:
            status = "❌ 测试失败"
            status_color = "red"
        else:
            status = "⚠️  部分跳过"
            status_color = "orange"
        
        # 格式化执行时长
        if duration < 60:
            duration_text = f"{duration:.2f}秒"
        elif duration < 3600:
            duration_text = f"{duration / 60:.2f}分钟"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            duration_text = f"{hours}小时{minutes}分钟"
        
        # 构建Markdown消息
        at_text = self._get_at_users()
        
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_content = f"""## {status}

**测试执行完成**

**执行时间:** {current_time}

---

### 📊 测试统计

- **总用例数:** {total}
- **通过:** {passed} ✅
- **失败:** {failed} ❌
- **中断:** {broken} ⚠️
- **跳过:** {skipped} ⏭️

### 📈 通过率

**{passed_rate:.1f}%** ({passed}/{total})

### ⏱️ 执行时长

{duration_text}

"""
        
        if report_url:
            # 如果是本地文件路径（以"本地报告路径:"开头），显示为文本说明
            if report_url.startswith("本地报告路径:"):
                report_path = report_url.replace("本地报告路径: ", "")
                markdown_content += f"\n### 📄 详细报告\n\n**本地报告路径：**\n`{report_path}`\n\n💡 请在本地浏览器中打开上述路径查看报告\n"
            else:
                # Jenkins 环境，使用可点击的链接
                markdown_content += f"\n### 📄 详细报告\n\n[🔗 查看完整报告]({report_url})\n"
        
        if at_text:
            markdown_content += f"\n{at_text}\n"
        
        # 构建消息体
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": "接口自动化测试报告",
                "text": markdown_content
            }
        }
        
        # 如果有@用户，添加at字段
        if self.at_mobiles or self.at_all:
            message["at"] = {
                "atMobiles": self.at_mobiles,
                "isAtAll": self.at_all
            }
        
        try:
            webhook_url = self._get_webhook_url()
            if not webhook_url:
                print("⚠️  无法获取有效的钉钉webhook URL")
                return False
            
            response = requests.post(
                webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print("✅ 钉钉通知发送成功")
                    return True
                else:
                    print(f"❌ 钉钉通知发送失败: {result.get('errmsg', '未知错误')}")
                    return False
            else:
                print(f"❌ 钉钉通知发送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 钉钉通知发送异常: {e}")
            return False
    
    def send_simple_message(self, title: str, content: str) -> bool:
        """
        发送简单文本消息到钉钉
        
        Args:
            title: 消息标题
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self.webhook_url:
            print("⚠️  钉钉webhook未配置，跳过钉钉通知")
            return False
        
        at_text = self._get_at_users()
        
        markdown_content = f"""## {title}

{content}

"""
        
        if at_text:
            markdown_content += f"\n{at_text}\n"
        
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": markdown_content
            }
        }
        
        if self.at_mobiles or self.at_all:
            message["at"] = {
                "atMobiles": self.at_mobiles,
                "isAtAll": self.at_all
            }
        
        try:
            webhook_url = self._get_webhook_url()
            if not webhook_url:
                print("⚠️  无法获取有效的钉钉webhook URL")
                return False
            
            response = requests.post(
                webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print("✅ 钉钉通知发送成功")
                    return True
                else:
                    print(f"❌ 钉钉通知发送失败: {result.get('errmsg', '未知错误')}")
                    return False
            else:
                print(f"❌ 钉钉通知发送失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 钉钉通知发送异常: {e}")
            return False
