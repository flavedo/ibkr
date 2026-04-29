"""
东方财富 (EastMoney) 经济日历 API 反查脚本

查找东方财富页面中的实际 AJAX / API 数据端点
"""

import json
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

EASTMONEY_URL = "https://forex.eastmoney.com/fc.html"


def find_api_endpoints():
    print("=" * 60)
    print("东方财富 API 端点反查")
    print("=" * 60)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://forex.eastmoney.com/",
    }

    r = requests.get(EASTMONEY_URL, headers=headers, timeout=15)
    r.encoding = "utf-8"
    html = r.text

    print(f"\n1. 页面大小: {len(html)} 字符")

    # 查找所有 script 标签内容
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script")
    print(f"\n2. Script 标签数: {len(scripts)}")

    for i, s in enumerate(scripts):
        content = s.string or ""
        if len(content) > 1000:
            # 检查是否包含 API/URL 相关模式
            patterns_to_check = [
                "api", "fetch", "ajax", "request", "url", "data", "calendar",
                "getData", "loadData", "getCalendar", "getList",
                "/Api/", "forex.eastmoney", "calendar",
            ]
            matched = [p for p in patterns_to_check if p.lower() in content.lower()]
            if matched:
                print(f"\n   脚本 #{i} (长度 {len(content)})")
                print(f"   匹配: {matched}")
                # 提取 URL
                urls = re.findall(r'https?://[^\s"\'<>]+', content)
                for u in urls:
                    if "calendar" in u.lower() or "api" in u.lower() or "data" in u.lower():
                        print(f"   候选 URL: {u}")

    # 直接搜索可能的 API 端点
    print(f"\n3. 搜索 API 模式:")
    patterns = [
        (r'/Api/Calendar/[^"\']+', "Calendar API"),
        (r'https?://[^"\']*calendar[^"\']*', "URL with calendar"),
        (r'getCalendarData|loadCalendarData|GetCalendarData', "CalendarData fn"),
        (r'\bapi/calendar\b', "api/calendar path"),
        (r'\bajax.*calendar\b', "ajax calendar"),
    ]

    for pattern, desc in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            for m in matches[:5]:
                # get some context
                idx = html.lower().index(m.lower())
                start = max(0, idx - 80)
                end = min(len(html), idx + len(m) + 80)
                ctx = html[start:end]
                print(f"   [{desc}] (pos {idx}): ...{ctx}...")

    print(f"\n4. 搜索 AJAX/数据加载代码:")
    loading_patterns = [
        r'\.ajax\s*\(',
        r'axios\.',
        r'fetch\s*\(',
        r'XMLHttpRequest',
        r'\$\.get\s*\(',
        r'\$\.post\s*\(',
    ]
    for pat in loading_patterns:
        if re.search(pat, html, re.IGNORECASE):
            # Found matches, show context
            for m in re.finditer(pat, html, re.IGNORECASE):
                start = max(0, m.start() - 150)
                end = min(len(html), m.end() + 250)
                ctx = html[start:end]
                # Clean up the context
                ctx_clean = ctx.replace("\n", " ").replace("\r", " ")
                print(f"\n   ...{ctx_clean}...")
                break  # just show first match
            break
    else:
        print("   未找到 AJAX 调用模式")

    print(f"\n5. 搜索 JSON 数据:")
    # Look for large JSON arrays or objects
    json_like = re.findall(r'\[\s*\{[^]]+\}\s*\]', html[:200000])  # limit search
    if json_like:
        print(f"   找到 {len(json_like)} 个疑似 JSON 数组")
        for j in json_like[:3]:
            try:
                data = json.loads(j)
                if isinstance(data, list) and len(data) > 3:
                    print(f"   有效 JSON: {len(data)} 条, 示例: {json.dumps(data[0], ensure_ascii=False)[:200]}")
            except (json.JSONDecodeError, ValueError):
                pass


def try_known_eastmoney_apis():
    """尝试已知的东方财富 API 端点"""
    print(f"\n{ '=' * 60 }")
    print("尝试已知的 EastMoney API 端点")
    print(f"{ '=' * 60 }")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://forex.eastmoney.com/",
    }

    candidates = [
        "https://forex.eastmoney.com/Api/Calendar/GetCalendarData",
        "https://push2.eastmoney.com/api/qt/ulist.np/get",
        "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "https://forex.eastmoney.com/ajax/calendar/getdata",
        "https://api.eastmoney.com/forex/calendar/list",
    ]

    for url in candidates:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            ct = r.headers.get("Content-Type", "")
            print(f"\n   {url}")
            print(f"   -> {r.status_code} | {ct[:50]}")
            if r.status_code == 200:
                text = r.text[:300]
                print(f"   -> {text}")
        except Exception as e:
            print(f"\n   {url}")
            print(f"   -> Error: {type(e).__name__}")


def main():
    find_api_endpoints()
    try_known_eastmoney_apis()


if __name__ == "__main__":
    main()
