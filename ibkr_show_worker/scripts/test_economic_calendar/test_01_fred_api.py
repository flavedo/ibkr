"""
FRED API (Federal Reserve Economic Data) 测试脚本

Endpoint: https://api.stlouisfed.org/fred/releases/dates
费用: 完全免费，需要注册获取 API Key
限制: 无明确速率限制（合理使用即可）
注册: https://fred.stlouisfed.org/docs/api/api_key.html

覆盖范围:
  - 美国经济数据发布日历（非农、CPI、GDP、失业率等）
  - 400,000+ 经济时间序列
  - 仅限美国数据

测试内容:
  1. 连接 FRED API
  2. 获取经济数据发布日历
  3. 检查返回的数据结构
  4. 评估是否适合项目使用
"""

import json
import sys
from datetime import datetime, timedelta

import requests

FRED_API_BASE = "https://api.stlouisfed.org/fred"


def get_api_key() -> str:
    """获取 FRED API Key"""
    import os
    key = os.environ.get("FRED_API_KEY", "")
    if not key:
        key = input("请输入 FRED API Key (免费申请: https://fred.stlouisfed.org/docs/api/api_key.html): ").strip()
    return key


def test_get_releases_dates(api_key: str) -> dict:
    """测试获取所有经济数据发布的日期"""
    url = f"{FRED_API_BASE}/releases/dates"
    params = {
        "api_key": api_key,
        "file_type": "json",
        "limit": 20,
        "sort_order": "desc",
        "include_release_dates_with_no_data": "false",
    }
    print(f"\n1. 请求 GET {url}")
    print(f"   参数: {params}")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"   状态码: {response.status_code}")
    print(f"   返回类型: {type(data).__name__}")
    return data


def test_get_releases_for_date_range(api_key: str) -> dict:
    """测试获取指定日期范围内的发布"""
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    url = f"{FRED_API_BASE}/releases/dates"
    params = {
        "api_key": api_key,
        "file_type": "json",
        "limit": 50,
        "realtime_start": start_date,
        "realtime_end": end_date,
        "sort_order": "asc",
        "include_release_dates_with_no_data": "false",
    }
    print(f"\n2. 请求未来 30 天的发布日历")
    print(f"   参数: {params}")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print(f"   状态码: {response.status_code}")
    return data


def test_get_specific_release(api_key: str, release_id: int = 170) -> dict:
    """测试获取特定发布详情（170 = Nonfarm Payrolls / Employment Situation）"""
    url = f"{FRED_API_BASE}/release"
    params = {
        "api_key": api_key,
        "file_type": "json",
        "release_id": str(release_id),
    }
    print(f"\n3. 获取发布详情 (release_id={release_id})")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    return data


def test_get_release_series(api_key: str, release_id: int = 170) -> dict:
    """测试获取发布下的所有数据序列"""
    url = f"{FRED_API_BASE}/release/series"
    params = {
        "api_key": api_key,
        "file_type": "json",
        "release_id": str(release_id),
        "limit": 5,
    }
    print(f"\n4. 获取发布下的数据序列 (release_id={release_id})")

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    return data


def evaluate_feasibility(data: dict) -> None:
    """评估 FRED API 是否适合本项目"""
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)

    release_dates = data.get("release_dates", [])
    if release_dates:
        sample = release_dates[0]
        print(f"\n✅ 返回数据示例:")
        print(f"   {json.dumps(sample, indent=4, ensure_ascii=False)}")

        required_fields = {"release_id", "release_name", "release_date"}
        has_fields = required_fields.issubset(sample.keys())
        print(f"\n核心字段完整性: {'✅ 完整' if has_fields else '⚠️ 部分缺失'}")
        if not has_fields:
            print(f"  实际字段: {list(sample.keys())}")

    print(f"\n✅ 优点:")
    print(f"   - 完全免费，注册即用")
    print(f"   - 数据权威，来自美联储")
    print(f"   - 覆盖美国所有重要经济数据发布")
    print(f"   - 包含 400,000+ 时间序列")
    print(f"   - API 稳定，多年未变")

    print(f"\n⚠️ 局限:")
    print(f"   - 仅覆盖美国经济数据")
    print(f"   - 不包含市场共识预期（consensus forecast）")
    print(f"   - 不包含 impact/high/low 影响等级标注")
    print(f"   - 需要注册 API Key")

    print(f"\n适合场景: 美国经济数据日历")
    print(f"不适合: 全球宏观经济日历、带预期值的日历")


def main():
    print("=" * 60)
    print("FRED API 可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")

    api_key = get_api_key()
    if not api_key:
        print("\n❌ 未提供 API Key。请先申请: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   申请后设置环境变量: export FRED_API_KEY=your_key_here")
        sys.exit(1)

    try:
        data = test_get_releases_dates(api_key)
        print(f"\n  返回数据概要:")
        release_dates = data.get("release_dates", [])
        print(f"  获取到 {len(release_dates)} 条发布记录")
        if release_dates:
            print(f"  最近发布: {release_dates[0]}")

        _ = test_get_releases_for_date_range(api_key)

        release_data = test_get_specific_release(api_key)
        print(f"\n  返回: {json.dumps(release_data, indent=2, ensure_ascii=False)[:300]}")

        series_data = test_get_release_series(api_key)
        print(f"\n  发布序列:")
        series_list = series_data.get("seriess", [])
        print(f"  获取到 {len(series_list)} 个序列")
        for s in series_list[:3]:
            print(f"    - {s.get('id')}: {s.get('title')}")

        evaluate_feasibility(data)

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误: {e}")
        if "401" in str(e):
            print("  可能是 API Key 无效，请检查: https://fred.stlouisfed.org/docs/api/api_key.html")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 无法访问 {FRED_API_BASE}")
        print("  请检查网络连接")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
