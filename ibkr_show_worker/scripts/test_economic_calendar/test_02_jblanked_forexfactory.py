"""
jblanked Forex Factory API 测试脚本

Endpoint: https://www.jblanked.com/news/api/forex-factory/calendar/
费用: 完全免费，无需 API Key
限制: 未知（第三方逆向封装，可能不稳定）

覆盖范围:
  - 全球宏观经济日历（非农、CPI、利率决议等）
  - 所有主要货币/国家（USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD）
  - 包含 impact（高/中/低）等级
  - 包含 previous/forecast/actual 数据

测试内容:
  1. 获取本周日历
  2. 按货币筛选
  3. 检查数据结构和完整性
  4. 评估是否适合项目使用
"""

import json
import sys
from datetime import datetime

import requests

BASE_URL = "https://www.jblanked.com/news/api"


def test_get_weekly_calendar() -> list:
    """测试获取本周经济日历"""
    url = f"{BASE_URL}/forex-factory/calendar/week"
    print(f"\n1. 请求 GET {url}")

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"   状态码: {response.status_code}")
    print(f"   返回类型: {type(data).__name__}")
    return data


def test_get_calendar_by_currency(currency: str = "USD") -> list:
    """测试按货币筛选日历"""
    url = f"{BASE_URL}/forex-factory/calendar/week"
    params = {"currency": currency}
    print(f"\n2. 请求按货币筛选: {currency}")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"   状态码: {response.status_code}")
    return data


def test_get_high_impact_only() -> list:
    """测试只获取高影响事件"""
    url = f"{BASE_URL}/forex-factory/calendar/week"
    params = {"impact": "High"}
    print(f"\n3. 请求仅高影响事件")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"   状态码: {response.status_code}")
    return data


def test_get_calendar_by_date_range() -> list:
    """测试获取特定日期范围"""
    today = datetime.now()
    # 尝试获取本月的日历
    month_str = today.strftime("%Y-%m")
    url = f"{BASE_URL}/forex-factory/calendar/month"
    params = {"month": month_str}
    print(f"\n4. 请求按月筛选: {month_str}")

    response = requests.get(url, params=params, timeout=15)
    if response.status_code == 200:
        data = response.json()
        print(f"   状态码: {response.status_code}")
        return data
    else:
        print(f"   状态码: {response.status_code} (月端点可能不存在)")
        print(f"   响应: {response.text[:200]}")
        return []


def evaluate_feasibility(sample_data: list) -> None:
    """评估 jblanked API 是否适合本项目"""
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)

    if not sample_data:
        print("\n❌ 未获取到数据")
        return

    sample = sample_data[0]
    print(f"\n✅ 返回数据示例 (共 {len(sample_data)} 条):")
    print(f"   {json.dumps(sample, indent=4, ensure_ascii=False)}")

    all_keys = set()
    for item in sample_data:
        all_keys.update(item.keys())
    print(f"\n全部字段: {sorted(all_keys)}")

    # 检查关键字段
    crucial_fields = {"title", "currency", "impact", "date", "time"}
    has_crucial = crucial_fields.issubset(all_keys)
    print(f"核心字段(标题/货币/影响/日期/时间): {'✅ 完整' if has_crucial else '⚠️ 缺失'}")

    forecast_fields = {"previous", "forecast", "actual"}
    has_forecast = forecast_fields.issubset(all_keys)
    print(f"预期字段(前值/预期/实际): {'✅ 完整' if has_forecast else '⚠️ 缺失'}")

    # 统计各影响等级
    impacts = {}
    currencies = set()
    for item in sample_data:
        imp = str(item.get("impact", "unknown"))
        impacts[imp] = impacts.get(imp, 0) + 1
        cur = item.get("currency", "")
        if cur:
            currencies.add(cur)

    print(f"\n影响等级分布: {impacts}")
    print(f"货币覆盖: {sorted(currencies)}")

    print(f"\n✅ 优点:")
    print(f"   - 完全免费，无需 API Key")
    print(f"   - 覆盖全球宏观经济日历")
    print(f"   - 包含 impact 高/中/低等级")
    print(f"   - 包含 previous/forecast/actual")
    print(f"   - 按货币、影响等级筛选")
    print(f"   - REST API，easy to use")

    print(f"\n⚠️ 局限:")
    print(f"   - 第三方封装服务，非官方 API")
    print(f"   - 可能不稳定或随时关闭")
    print(f"   - 数据来源为 Forex Factory，延迟可能 5-15 分钟")
    print(f"   - 无 SLA 保证")

    print(f"\n适合场景: 轻量级宏观经济日历、个人项目")
    print(f"适合场景: 需要全球经济事件 + impact 标注的场景")


def main():
    print("=" * 60)
    print("jblanked Forex Factory API 可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")

    try:
        weekly_data = test_get_weekly_calendar()
        print(f"\n  本周获取到 {len(weekly_data)} 条事件")
        if weekly_data:
            print(f"  第一条: {json.dumps(weekly_data[0], indent=2, ensure_ascii=False)}")

        usd_data = test_get_calendar_by_currency("USD")
        print(f"\n  USD 事件: {len(usd_data)} 条")

        high_data = test_get_high_impact_only()
        print(f"\n  高影响事件: {len(high_data)} 条")

        monthly_data = test_get_calendar_by_date_range()

        best_sample = weekly_data or usd_data or high_data or monthly_data
        evaluate_feasibility(best_sample)

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误: {e}")
        if "404" in str(e):
            print("  API 端点可能已变更")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 无法访问 {BASE_URL}")
        print("  请检查网络连接")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 解析失败: {e}")
        print("  响应可能不是有效的 JSON 格式")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
