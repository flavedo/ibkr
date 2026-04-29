"""
yfinance Calendars 测试脚本

Endpoint: yfinance.Calendars (内部使用 Yahoo Finance)
费用: 完全免费，无需 API Key
限制: 无官方限制（实际受 Yahoo Finance 速率限制）

覆盖范围:
  - Earnings Calendar（财报日历）
  - IPO Calendar
  - Economic Events Calendar（经济事件日历）
  - Splits Calendar（拆股日历）

注意: 需要安装 yfinance: pip install yfinance

测试内容:
  1. 获取经济事件日历
  2. 获取财报日历
  3. 检查数据结构和完整性
  4. 评估是否适合项目使用
"""

import json
import sys
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    print("❌ 需要安装 yfinance: pip install yfinance")
    sys.exit(1)


def test_get_economic_calendar():
    """测试获取经济事件日历"""
    today = datetime.now()
    start = today.strftime("%Y-%m-%d")
    end = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"\n1. 获取经济事件日历")
    print(f"   范围: {start} ~ {end}")

    try:
        calendars = yf.Calendars(start=start, end=end)
        data = calendars.get_economic_events_calendar()
        print(f"   返回类型: {type(data).__name__}")
        return data
    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_earnings_calendar():
    """测试获取财报日历"""
    today = datetime.now()
    start = today.strftime("%Y-%m-%d")
    end = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"\n2. 获取 Earnings 日历")
    print(f"   范围: {start} ~ {end}")

    try:
        calendars = yf.Calendars(start=start, end=end)
        data = calendars.get_earnings_calendar()
        print(f"   返回类型: {type(data).__name__}")
        return data
    except Exception as e:
        print(f"   错误: {e}")
        return None


def test_get_ipo_calendar():
    """测试获取 IPO 日历"""
    today = datetime.now()
    start = today.strftime("%Y-%m-%d")
    end = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"\n3. 获取 IPO 日历")
    print(f"   范围: {start} ~ {end}")

    try:
        calendars = yf.Calendars(start=start, end=end)
        data = calendars.get_ipo_info_calendar()
        print(f"   返回类型: {type(data).__name__}")
        return data
    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def evaluate_feasibility(economic_data, earnings_data, ipo_data) -> None:
    """评估 yfinance 是否适合本项目"""
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)

    print(f"\n📊 经济事件日历:")
    if economic_data is not None:
        print(f"   类型: {type(economic_data).__name__}")
        if hasattr(economic_data, 'shape'):
            print(f"   行数: {economic_data.shape[0]}")
            print(f"   列: {list(economic_data.columns)}")
        elif isinstance(economic_data, dict):
            print(f"   键: {list(economic_data.keys())[:10]}")
        elif isinstance(economic_data, list):
            print(f"   条数: {len(economic_data)}")
            if economic_data:
                print(f"   第一条: {json.dumps(economic_data[0], indent=2, ensure_ascii=False)[:300]}")
        else:
            print(f"   数据样例: {str(economic_data)[:300]}")
    else:
        print(f"   ❌ 获取失败")

    print(f"\n📈 Earnings 日历:")
    if earnings_data is not None:
        print(f"   类型: {type(earnings_data).__name__}")
        if hasattr(earnings_data, 'shape'):
            print(f"   行数: {earnings_data.shape[0]}")
            print(f"   列: {list(earnings_data.columns)}")
            if earnings_data.shape[0] > 0:
                print(f"   第一条: {earnings_data.iloc[0].to_dict()}")
        elif isinstance(earnings_data, dict):
            print(f"   键: {list(earnings_data.keys())[:10]}")
        elif isinstance(earnings_data, list):
            print(f"   条数: {len(earnings_data)}")
    else:
        print(f"   ❌ 获取失败")

    print(f"\n🏢 IPO 日历:")
    if ipo_data is not None:
        print(f"   类型: {type(ipo_data).__name__}")
        if hasattr(ipo_data, 'shape'):
            print(f"   行数: {ipo_data.shape[0]}")
            print(f"   列: {list(ipo_data.columns)}")
    else:
        print(f"   ❌ 获取失败")

    print(f"\n✅ 优点:")
    print(f"   - 完全免费，无需注册")
    print(f"   - 覆盖 Earnings / IPO / Economic Events / Splits")
    print(f"   - Python 原生库，集成简单")
    print(f"   - yfinance 社区活跃，维护良好")

    print(f"\n⚠️ 局限:")
    print(f"   - Yahoo Finance 底层，数据可能不完整")
    print(f"   - 经济事件日历相对基础")
    print(f"   - 不含 impact 等级标注")
    print(f"   - 速率限制不透明")
    print(f"   - 需要安装 yfinance 依赖")
    print(f"   - Economic Calendars  API 较新，稳定性待验证")

    print(f"\n适合场景: 需要 Earnings 日历为主，经济事件为辅")
    print(f"适合场景: 已经在用 yfinance 的项目")


def main():
    print("=" * 60)
    print("yfinance Calendars 可行性测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    print(f"yfinance 版本: {yf.__version__}")

    economic_data = test_get_economic_calendar()
    earnings_data = test_get_earnings_calendar()
    ipo_data = test_get_ipo_calendar()

    evaluate_feasibility(economic_data, earnings_data, ipo_data)


if __name__ == "__main__":
    main()
