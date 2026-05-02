"""
市场情绪数据源测试脚本

测试两个数据源:
  1. VIX 波动率指数 — 通过 yfinance 获取 ^VIX 最新值
  2. Fear & Greed Index — 通过 alternative.me API 获取

费用: 均免费, 无需 API Key
"""

import json
import sys
from datetime import datetime


def test_vix():
    """测试通过 yfinance 获取 VIX 最新值"""
    print("\n" + "=" * 60)
    print("1. VIX 波动率指数 (yfinance ^VIX)")
    print("=" * 60)

    try:
        import yfinance as yf
    except ImportError:
        print("   需要安装 yfinance: pip install yfinance")
        return None

    try:
        ticker = yf.Ticker("^VIX")
        df = ticker.history(period="5d")

        if df is None or df.empty:
            print("   返回数据为空")
            return None

        latest = df.iloc[-1]
        vix_value = float(latest["Close"])
        date = df.index[-1]

        print(f"   状态码: OK")
        print(f"   数据行数: {len(df)}")
        print(f"   最新日期: {date}")
        print(f"   VIX 收盘价: {vix_value:.2f}")
        print(f"   开盘: {latest['Open']:.2f}")
        print(f"   最高: {latest['High']:.2f}")
        print(f"   最低: {latest['Low']:.2f}")

        print(f"\n   最近 5 日数据:")
        for idx, row in df.iterrows():
            print(f"     {idx.strftime('%Y-%m-%d')}  Open={row['Open']:.2f}  High={row['High']:.2f}  Low={row['Low']:.2f}  Close={row['Close']:.2f}")

        return vix_value
    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fear_greed():
    """测试通过 alternative.me API 获取 Fear & Greed 指数"""
    print("\n" + "=" * 60)
    print("2. Fear & Greed Index (alternative.me)")
    print("=" * 60)

    import requests

    url = "https://api.alternative.me/fng/?limit=7"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   URL: {url}")
        print(f"   状态码: {response.status_code}")

        if response.status_code != 200:
            print(f"   HTTP 错误: {response.status_code}")
            return None

        data = response.json()

        entries = data.get("data", [])
        metadata = data.get("metadata", {})

        print(f"   返回条数: {len(entries)}")
        print(f"   Metadata: {json.dumps(metadata, ensure_ascii=False)}")

        if not entries:
            print("   无数据返回")
            return None

        print(f"\n   最近 {len(entries)} 条记录:")
        for entry in entries:
            value = int(entry["value"])
            classification = entry.get("value_classification", "")
            timestamp = int(entry["timestamp"])
            dt = datetime.fromtimestamp(timestamp)
            print(f"     {dt.strftime('%Y-%m-%d')}  F&G={value:>3}  [{classification}]")

        latest = entries[0]
        latest_value = int(latest["value"])
        latest_class = latest.get("value_classification", "")

        print(f"\n   最新值: {latest_value} ({latest_class})")

        return {
            "value": latest_value,
            "classification": latest_class,
            "history": entries,
        }

    except requests.exceptions.Timeout:
        print("   请求超时 (15s)")
        return None
    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def evaluate_vix_range(vix_value):
    """根据截图中的区间定义评估 VIX 所处位置"""
    ranges = [
        ("< 12", 0, 12, "极度乐观", "#4ade80"),
        ("12—20", 12, 20, "正常区间", "#22c55e"),
        ("20—30", 20, 30, "恐惧上升", "#fbbf24"),
        ("30—50", 30, 50, "市场恐慌", "#f97316"),
        ("> 50", 50, 999, "极度恐惧", "#ef4444"),
    ]

    print("\n" + "=" * 60)
    print("3. VIX 区间判定")
    print("=" * 60)

    if vix_value is None:
        print("   无法判定 (无 VIX 数据)")
        return

    print(f"   当前 VIX: {vix_value:.2f}")
    print(f"   区间色条:")

    for label, lo, hi, sentiment, color in ranges:
        in_range = lo <= vix_value < hi
        marker = "▼" if in_range else "──"
        bar_width = 10
        block = "█" * bar_width if in_range else "░" * bar_width
        current_tag = " ◄ NOW" if in_range else ""
        print(f"     {marker} {block}  {label:>6}  {sentiment}{current_tag}")


def evaluate_fear_greed_range(fg_data):
    """根据截图中的区间定义评估 Fear & Greed 所处位置"""
    ranges = [
        ("0—24", 0, 25, "极度恐惧", "#ef4444"),
        ("25—44", 25, 45, "恐惧", "#f97316"),
        ("45—55", 45, 56, "中性", "#93c5fd"),
        ("56—75", 56, 76, "贪婪", "#fbbf24"),
        ("76—100", 76, 101, "极度贪婪", "#22c55e"),
    ]

    print("\n" + "=" * 60)
    print("4. Fear & Greed 区间判定")
    print("=" * 60)

    if fg_data is None:
        print("   无法判定 (无 F&G 数据)")
        return

    value = fg_data["value"]
    print(f"   当前 F&G: {value}")
    print(f"   区间色条:")

    for label, lo, hi, sentiment, color in ranges:
        in_range = lo <= value < hi
        marker = "▼" if in_range else "──"
        bar_width = 10
        block = "█" * bar_width if in_range else "░" * bar_width
        current_tag = " ◄ NOW" if in_range else ""
        print(f"     {marker} {block}  {label:>6}  {sentiment}{current_tag}")


def main():
    print("=" * 60)
    print("  市场情绪数据源可行性测试")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    vix = test_vix()
    fg = test_fear_greed()

    evaluate_vix_range(vix)
    evaluate_fear_greed_range(fg)

    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)

    results = []
    if vix is not None:
        results.append(("VIX (yfinance)", True, f"最新值 {vix:.2f}"))
    else:
        results.append(("VIX (yfinance)", False, "获取失败"))

    if fg is not None:
        results.append(("Fear & Greed (alt.me)", True, f"最新值 {fg['value']} ({fg['classification']})"))
    else:
        results.append(("Fear & Greed (alt.me)", False, "获取失败"))

    all_ok = all(ok for _, ok, _ in results)

    for name, ok, desc in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {status}  {name}: {desc}")

    if all_ok:
        print("\n  结论: 两个数据源均可用，可以集成到项目中 ✅")
    else:
        print("\n  结论: 存在不可用数据源，需要排查 ⚠️")


if __name__ == "__main__":
    main()
