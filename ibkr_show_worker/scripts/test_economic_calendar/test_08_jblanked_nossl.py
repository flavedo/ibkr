"""
jblanked News API 测试（禁用 SSL 验证）

尝试不同的 jblanked API 端点
"""

import json
import sys
from datetime import datetime

import requests
import urllib3
urllib3.disable_warnings()

HEADERS = {"User-Agent": "Mozilla/5.0"}

ENDPOINTS = [
    ("forex-factory weekly", "https://www.jblanked.com/news/api/forex-factory/calendar/week/"),
    ("forex-factory today", "https://www.jblanked.com/news/api/forex-factory/calendar/today/"),
    ("mql5 weekly", "https://www.jblanked.com/news/api/mql5/calendar/week/"),
    ("fxstreet weekly", "https://www.jblanked.com/news/api/fxstreet/calendar/week/"),
    ("all weekly", "https://www.jblanked.com/news/api/calendar/week/"),
]


def main():
    print("=" * 60)
    print("jblanked News API 端点测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    print()

    for name, url in ENDPOINTS:
        print(f"\n[{name}]")
        print(f"  URL: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            print(f"  状态码: {r.status_code}")
            print(f"  响应头 Content-Type: {r.headers.get('Content-Type', 'N/A')}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    if isinstance(data, list):
                        print(f"  事件数: {len(data)}")
                        if data:
                            print(f"  字段: {list(data[0].keys())}")
                            print(f"  示例: {json.dumps(data[0], ensure_ascii=False, indent=2)}")
                    else:
                        print(f"  返回类型: {type(data).__name__}")
                        print(f"  内容: {json.dumps(data, ensure_ascii=False)[:500]}")
                except json.JSONDecodeError:
                    print(f"  非 JSON 响应 (前300字符): {r.text[:300]}")
            else:
                print(f"  响应: {r.text[:200]}")
        except requests.exceptions.SSLError as e:
            print(f"  SSL 错误: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"  连接错误: {e}")
        except requests.exceptions.Timeout:
            print(f"  超时 (20s)")
        except Exception as e:
            print(f"  未知错误: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
