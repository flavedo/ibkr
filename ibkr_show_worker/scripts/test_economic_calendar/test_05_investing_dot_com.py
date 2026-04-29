"""
Investing.com 经济日历爬虫测试脚本

方法: Web scraping（非官方 API）
费用: 免费
限制: 违反 ToS、IP 可能被封锁

覆盖范围:
  - 全球宏观经济日历
  - 所有主要国家
  - 包含 impact 等级
  - 包含 previous/forecast/actual

注意: 需要安装: pip install beautifulsoup4 lxml

测试内容:
  1. 尝试获取 Investing.com 经济日历
  2. 检查是否被反爬拦截
  3. 对比 jblanked API 的可行性和稳定性
  4. 评估是否适合项目使用
"""

import json
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ 需要安装 requests: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ 需要安装 beautifulsoup4: pip install beautifulsoup4")
    sys.exit(1)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.investing.com/",
}


def test_get_calendar_page() -> str:
    """测试获取经济日历页面"""
    url = "https://www.investing.com/economic-calendar/"
    print(f"\n1. 请求 GET {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Length: {len(response.text)} 字符")
        print(f"   Cookies: {len(response.cookies)} 个")

        if "Just a moment" in response.text or "cf-browser-verification" in response.text:
            print("   ⚠️ Cloudflare 反爬拦截")
            return ""

        return response.text
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时 (20s)")
        return ""
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return ""


def test_get_calendar_via_api() -> dict:
    """测试通过 Investing.com 的 internal API 获取"""
    url = "https://ec.investing.com/api/calendar"
    headers = {
        **HEADERS,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    print(f"\n2. 尝试 internal API: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"   响应前 500 字符: {response.text[:500]}")
        if response.status_code == 200 and response.text.strip():
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"raw": response.text[:500]}
        return {}
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return {}


def test_investpy_library() -> bool:
    """测试是否可以通过 investpy 库获取"""
    print(f"\n3. 尝试 investpy 库")
    try:
        import investpy
        print(f"   investpy 版本: {investpy.__version__}")
        try:
            calendar = investpy.economic_calendar()
            print(f"   获取到 {len(calendar)} 条事件")
            if len(calendar) > 0:
                print(f"   第一条: {calendar.iloc[0].to_dict()}")
            return True
        except Exception as e:
            print(f"   ⚠️ investpy 经济日历报错: {e}")
            return False
    except ImportError:
        print(f"   ⚠️ investpy 未安装 (pip install investpy)")
        return False


def try_alternate_endpoints() -> dict:
    """尝试其他可能的 API 端点"""
    print(f"\n4. 尝试备选端点")

    candidates = [
        ("https://economic-calendar-api.com/api/v1/events", "generic"),
        ("https://api.forexfactory.com/calendar", "forexfactory"),
    ]

    for url, name in candidates:
        print(f"\n   尝试 {name}: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    return data
                except json.JSONDecodeError:
                    print(f"   非 JSON 响应: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

    return {}


def evaluate_feasibility(html: str, api_data: dict, has_investpy: bool) -> None:
    """评估 Investing.com 是否适合本项目"""
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)

    cloudflare_blocked = "Just a moment" in html or "cf-browser-verification" in html
    can_access = bool(html) and not cloudflare_blocked

    print(f"\n基本情况:")
    print(f"  页面可访问: {'✅' if can_access else '❌'}")
    print(f"  Cloudflare 拦截: {'✅ 被拦截' if cloudflare_blocked else '✅ 未被拦截'}")
    print(f"  Internal API 可用: {'✅' if api_data else '❌'}")
    print(f"  investpy 库: {'✅ 可用' if has_investpy else '❌ 不可用'}")

    print(f"\n✅ 优点:")
    print(f"   - 全球最全面的经济日历")
    print(f"   - 包含 impact 等级、共识预期等")

    print(f"\n⚠️ 局限:")
    if cloudflare_blocked:
        print(f"   - ❌ Cloudflare 反爬拦截严重")
    print(f"   - ❌ Web scraping 违反 ToS")
    print(f"   - ❌ 页面结构随时可能变化")
    print(f"   - ❌ IP 可能被封禁")
    print(f"   - investpy 库可能过时不可用")

    print(f"\n适合场景: 不推荐用于生产环境")
    print(f"推荐: 使用 jblanked API（它封装了 Forex Factory 数据）")


def main():
    print("=" * 60)
    print("Investing.com / 爬虫方案 可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")

    html = test_get_calendar_page()
    api_data = test_get_calendar_via_api()
    has_investpy = test_investpy_library()
    alt_data = try_alternate_endpoints()

    evaluate_feasibility(html, api_data, has_investpy)


if __name__ == "__main__":
    main()
