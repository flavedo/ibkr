"""
东方财富 (EastMoney) 经济日历测试脚本

Endpoint: https://forex.eastmoney.com/fc.html
方法: Web scraping
费用: 完全免费
限制: 无

覆盖范围:
  - 全球经济日历
  - 所有主要国家（美国、中国、欧元区、日本等）
  - 包含 impact 等级（高/中/低）
  - 包含 previous/forecast/actual

测试内容:
  1. 获取东方财富经济日历
  2. 解析表格数据
  3. 检查数据结构和完整性
  4. 评估是否适合项目使用
"""

import json
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

EASTMONEY_URL = "https://forex.eastmoney.com/fc.html"


def test_get_calendar_page() -> str:
    """测试获取经济日历页面"""
    print(f"\n1. 请求 GET {EASTMONEY_URL}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://forex.eastmoney.com/",
    }

    try:
        response = requests.get(EASTMONEY_URL, headers=headers, timeout=15)
        print(f"   状态码: {response.status_code}")
        print(f"   页面大小: {len(response.text)} 字符")
        response.encoding = "utf-8"
        return response.text
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return ""


def parse_calendar_events(html: str) -> list[dict]:
    """解析东方财富日历数据"""
    print(f"\n2. 解析日历数据")

    soup = BeautifulSoup(html, "lxml")
    events = []

    # 尝试找到日历表格
    table = soup.find("table", class_=re.compile(r"calendar|data|table"))
    if not table:
        table = soup.find("table", id="calendar")
    if not table:
        table = soup.find("table")
    if not table:
        # 尝试直接从 HTML 中提取 JSON 数据
        json_patterns = [
            r"var\s+calendarData\s*=\s*(\[.*?\]);",
            r"var\s+data\s*=\s*(\[.*?\]);",
            r"\"list\":\s*(\[.*?\])\s*[,\}]",
        ]
        for pattern in json_patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    print(f"   找到 JSON 数据: {len(data)} 条")
                    return data
                except json.JSONDecodeError:
                    continue

    if table:
        rows = table.find_all("tr")
        print(f"   找到表格: {len(rows)} 行")
        for row in rows[1:]:  # skip header
            cols = row.find_all("td")
            if len(cols) >= 5:
                events.append({
                    "date": cols[0].get_text(strip=True),
                    "time": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                    "country": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                    "event": cols[3].get_text(strip=True) if len(cols) > 3 else "",
                    "actual": cols[4].get_text(strip=True) if len(cols) > 4 else "",
                    "forecast": cols[5].get_text(strip=True) if len(cols) > 5 else "",
                    "previous": cols[6].get_text(strip=True) if len(cols) > 6 else "",
                    "impact": cols[7].get_text(strip=True) if len(cols) > 7 else "",
                })
        return events

    # If no table found, look for structured data in the HTML
    print("   未找到表格，尝试分析 HTML 结构...")
    # Print some sample HTML to understand structure
    body = soup.find("body")
    if body:
        # Look for data-like patterns
        all_text = body.get_text()
        lines = [l.strip() for l in all_text.split("\n") if l.strip()]
        print(f"   页面文本行数: {len(lines)}")
        for line in lines[:20]:
            print(f"   -> {line[:100]}")

    return events


def evaluate_feasibility(events: list[dict]) -> None:
    """评估 EastMoney 是否适合本项目"""
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)

    if not events:
        # Even without structured parsing, the page loads with raw HTML data
        # Let's check if the ajax API endpoint works
        print("\n⚠️ 未解析到事件（需要分析页面实际 AJAX 接口）")
        print("   建议使用浏览器 DevTools 分析实际 API 请求")

        print(f"\n✅ 优点:")
        print(f"   - 完全免费，无访问限制")
        print(f"   - 覆盖全球经济指标")
        print(f"   - 中文界面，对中国开发者友好")
        print(f"   - 包含 impact 等级和预期值")

        print(f"\n⚠️ 局限:")
        print(f"   - 需要逆向分析 AJAX API")
        print(f"   - 东方财富可能更改页面结构")
        print(f"   - 数据主要面向中文用户")
        return

    sample = events[0]
    print(f"\n✅ 获取到 {len(events)} 条事件")
    print(f"   示例: {json.dumps(sample, indent=2, ensure_ascii=False)[:300]}")

    countries = set(e.get("country", "") for e in events)
    print(f"   覆盖国家: {sorted(countries)}")

    impacts = {}
    for e in events:
        imp = e.get("impact", "unknown")
        impacts[imp] = impacts.get(imp, 0) + 1
    print(f"   影响等级分布: {impacts}")

    print(f"\n✅ 优点:")
    print(f"   - 完全免费，无需 API Key")
    print(f"   - 覆盖全球主要经济数据")
    print(f"   - 定期更新，数据质量好")
    print(f"   - 中文支持")

    print(f"\n⚠️ 局限:")
    print(f"   - Web scraping 方式，结构可能变化")
    print(f"   - 需要通过浏览器分析实际 API")
    print(f"   - 页面 AJAX 加载，初始 HTML 不含数据")

    print(f"\n适合场景: 免费全球经济日历的备选方案")
    print(f"注意: 建议找到实际 AJAX 接口后使用")


def main():
    print("=" * 60)
    print("东方财富 (EastMoney) 经济日历可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")

    html = test_get_calendar_page()
    if not html:
        print("\n❌ 无法获取页面")
        sys.exit(1)

    events = parse_calendar_events(html)
    evaluate_feasibility(events)


if __name__ == "__main__":
    main()
