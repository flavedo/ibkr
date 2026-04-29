"""
Alpha Vantage API 测试脚本

Endpoint: https://www.alphavantage.co/query
费用: 免费（25 次/天），需注册获取 API Key
注册: https://www.alphavantage.co/support/#api-key

覆盖范围:
  - 美国经济指标（GDP、CPI、失业率等）
  - Earnings Calendar（财报日历）
  - IPO Calendar
  - 注意: 没有统一的"经济日历"端点，只有单个指标的查询

测试内容:
  1. 获取 CPI 数据
  2. 获取 GDP 数据
  3. 获取 Earnings Calendar
  4. 检查数据结构和完整性
  5. 评估是否适合项目使用
"""

import json
import sys
from datetime import datetime

import requests

API_BASE = "https://www.alphavantage.co/query"


def get_api_key() -> str:
    """获取 Alpha Vantage API Key"""
    import os
    key = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
    if not key:
        key = input("请输入 Alpha Vantage API Key (免费: https://www.alphavantage.co/support/#api-key): ").strip()
    return key


def test_get_economic_indicator(api_key: str, function: str, name: str) -> dict:
    """测试获取经济指标"""
    print(f"\n1. 获取经济指标: {name} (function={function})")

    params = {
        "function": function,
        "apikey": api_key,
    }
    response = requests.get(API_BASE, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"   状态码: {response.status_code}")
    if "Note" in data:
        print(f"   ⚠️ API 限制: {data['Note'][:100]}")
    return data


def test_get_earnings_calendar(api_key: str) -> dict:
    """测试获取 Earnings Calendar"""
    print(f"\n2. 获取 Earnings Calendar")

    params = {
        "function": "EARNINGS_CALENDAR",
        "horizon": "3month",
        "apikey": api_key,
    }
    response = requests.get(API_BASE, params=params, timeout=15)
    response.raise_for_status()

    # Alpha Vantage returns CSV for earnings calendar
    print(f"   状态码: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
    print(f"   前 500 字符: {response.text[:500]}")
    return {"raw": response.text}


def test_get_ipo_calendar(api_key: str) -> dict:
    """测试获取 IPO Calendar"""
    print(f"\n3. 获取 IPO Calendar")

    params = {
        "function": "IPO_CALENDAR",
        "apikey": api_key,
    }
    response = requests.get(API_BASE, params=params, timeout=15)
    response.raise_for_status()

    print(f"   状态码: {response.status_code}")
    print(f"   前 500 字符: {response.text[:500]}")
    return {"raw": response.text}


def evaluate_feasibility(cpi_data: dict, gdp_data: dict) -> None:
    """评估 Alpha Vantage 是否适合本项目"""
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)

    print(f"\n✅ 经济指标示例 (CPI):")
    if "data" in cpi_data:
        print(f"   {json.dumps(cpi_data['data'][:2], indent=2, ensure_ascii=False)}")
    elif "Information" in cpi_data:
        print(f"   ℹ️ {cpi_data['Information']}")
    else:
        print(f"   {json.dumps(cpi_data, indent=2, ensure_ascii=False)[:300]}")

    print(f"\n✅ 优点:")
    print(f"   - 免费（25 次/天）")
    print(f"   - 有 Earnings Calendar 和 IPO Calendar")
    print(f"   - 有美国经济指标（CPI, GDP, 失业率等）")

    print(f"\n⚠️ 局限:")
    print(f"   - ❌ 没有统一的经济日历 API")
    print(f"   - ❌ 免费版 25 次/天，远远不够用")
    print(f"   - ❌ 经济指标只能查历史值，没有发布日期预告")
    print(f"   - ❌ Earnings Calendar 返回 CSV 而非 JSON")
    print(f"   - 没有 impact 等级标注")
    print(f"   - 没有共识预测值")

    print(f"\n适合场景: 获取单个经济指标的历史数据")
    print(f"不适合: 经济日历（缺乏发布日期预告和共识预期）")


def main():
    print("=" * 60)
    print("Alpha Vantage API 可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")

    api_key = get_api_key()
    if not api_key:
        print("\n❌ 未提供 API Key。请先申请: https://www.alphavantage.co/support/#api-key")
        sys.exit(1)

    try:
        cpi_data = test_get_economic_indicator(api_key, "CPI", "CPI (消费者物价指数)")
        gdp_data = test_get_economic_indicator(api_key, "REAL_GDP", "GDP (国内生产总值)")

        earnings = test_get_earnings_calendar(api_key)
        ipo = test_get_ipo_calendar(api_key)

        evaluate_feasibility(cpi_data, gdp_data)

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 无法访问 {API_BASE}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
