#!/usr/bin/env bash
#
# 经济日历 API 测试运行脚本
# 依次运行所有测试脚本并汇总结果
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          经济日历 API 可行性测试套件                        ║"
echo "║          测试时间: $(date '+%Y-%m-%d %H:%M:%S')              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

RESULTS=()

# ============================================================
# 测试 1: jblanked Forex Factory API (无需 API Key)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [1/5] jblanked Forex Factory API (无需 API Key)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if python3 test_02_jblanked_forexfactory.py 2>&1; then
    RESULTS+=("✅ jblanked Forex Factory: 通过")
else
    RESULTS+=("❌ jblanked Forex Factory: 失败")
fi

# ============================================================
# 测试 2: yfinance Calendars (需安装 yfinance)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [2/5] yfinance Calendars (需 pip install yfinance)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if python3 test_03_yfinance_calendars.py 2>&1; then
    RESULTS+=("✅ yfinance Calendars: 通过")
else
    RESULTS+=("❌ yfinance Calendars: 失败")
fi

# ============================================================
# 测试 3: FRED API (需 API Key)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [3/5] FRED API (需 FRED_API_KEY 环境变量)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if python3 test_01_fred_api.py 2>&1; then
    RESULTS+=("✅ FRED API: 通过")
else
    RESULTS+=("❌ FRED API: 失败")
fi

# ============================================================
# 测试 4: Alpha Vantage API (需 API Key)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [4/5] Alpha Vantage API (需 ALPHA_VANTAGE_API_KEY)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if python3 test_04_alpha_vantage.py 2>&1; then
    RESULTS+=("✅ Alpha Vantage: 通过")
else
    RESULTS+=("❌ Alpha Vantage: 失败")
fi

# ============================================================
# 测试 5: Investing.com (无需 Key, 可能被反爬)
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [5/5] Investing.com 爬虫 / 备选方案"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if python3 test_05_investing_dot_com.py 2>&1; then
    RESULTS+=("✅ Investing.com: 可通过")
else
    RESULTS+=("❌ Investing.com: 失败")
fi

# ============================================================
# 汇总
# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  测试结果汇总                                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
for result in "${RESULTS[@]}"; do
    echo "  $result"
done
echo ""
echo "详细结果请查看各脚本输出的 JSON 数据。"
echo ""
