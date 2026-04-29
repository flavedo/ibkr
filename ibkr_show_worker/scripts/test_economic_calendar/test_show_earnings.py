import yfinance as yf
from datetime import datetime
import pandas as pd

today = datetime.now()
year = today.year
month = today.month

month_start = today.replace(day=1).strftime("%Y-%m-%d")
if month == 12:
    month_end = f"{year + 1}-01-01"
else:
    month_end = f"{year}-{month + 1:02d}-01"

cal = yf.Calendars(start=month_start, end=month_end)

# ====== 1. 财报日历 ======
earn = cal.get_earnings_calendar()
print(f"\n{'='*60}")
print(f"📈 {year}年{month}月 美股财报日历")
print(f"{'='*60}")
print(f"{'公司':<28s} {'市值':>12s} {'事件':<44s} {'日期':<12s} {'时段':<6s} {'EPS预估':>8s}")
print("-" * 120)

for _, row in earn.iterrows():
    date_val = row["Event Start Date"]
    date_str = date_val.strftime("%m-%d %H:%M") if hasattr(date_val, "strftime") else str(date_val)[:16]
    eps_val = row.get("EPS Estimate")
    eps = f"${eps_val:.2f}" if pd.notna(eps_val) else "N/A"
    cap_val = row.get("Marketcap")
    cap = f"${cap_val / 1e9:.1f}B" if pd.notna(cap_val) else "N/A"
    timing = str(row.get("Timing", ""))
    company = str(row["Company"])
    event = str(row["Event Name"])
    if event == "nan":
        event = "(财报)"
    print(f"{company:<28s} {cap:>12s} {event:<44s} {date_str:<12s} {timing:<6s} {eps:>8s}")

print(f"\n总计 {len(earn)} 条 | " + f"盘后(AMC): {(earn['Timing']=='AMC').sum()} | " + f"盘中(TAS): {(earn['Timing']=='TAS').sum()}")

# ====== 2. 经济事件日历 ======
eco = cal.get_economic_events_calendar()
print(f"\n{'='*60}")
print(f"📊 {year}年{month}月 经济事件日历 (Yahoo Finance)")
print(f"{'='*60}")

major_regions = {"US", "GB", "CN", "JP", "DE", "FR", "EU", "EZ", "AU", "CA", "CH", "KR", "IN"}
eco_filtered = eco[eco["Region"].isin(major_regions)]

if len(eco_filtered) > 0:
    print(f"{'地区':<6s} {'时间':<22s} {'对应月份':<12s} {'实际值':>10s} {'预期值':>10s} {'前值':>10s}")
    print("-" * 75)
    for _, row in eco_filtered.iterrows():
        t = row["Event Time"]
        time_str = t.strftime("%m-%d %H:%M") if hasattr(t, "strftime") else str(t)
        actual = f"{row['Actual']:.2f}" if pd.notna(row["Actual"]) else "-"
        expected = f"{row['Expected']:.2f}" if pd.notna(row["Expected"]) else "-"
        last = f"{row['Last']:.2f}" if pd.notna(row["Last"]) else "-"
        print(f"{str(row['Region']):<6s} {time_str:<22s} {str(row['For']):<12s} {actual:>10s} {expected:>10s} {last:>10s}")
else:
    print("(本月无主要经济体的事件数据)")

print(f"\n全部地区: {sorted(eco['Region'].unique())}")
print(f"共 {len(eco)} 条, 主要经济体 {len(eco_filtered)} 条")

# ====== 3. 美股重要事件按日汇总 ======
print(f"\n{'='*60}")
print(f"📅 {year}年{month}月 美股重点日期")
print(f"{'='*60}")

earn["day"] = earn["Event Start Date"].dt.day
for day in sorted(earn["day"].unique()):
    day_earn = earn[earn["day"] == day]
    companies = [str(c) for c in day_earn["Company"]]
    print(f"\n  {month}月{day}日:")
    for c in companies:
        print(f"    📊 {c}")
