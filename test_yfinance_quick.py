import yfinance as yf
from datetime import datetime, timedelta

start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
end = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

print("测试 yfinance 经济事件...")
cal = yf.Calendars(start=start, end=end)
df = cal.get_economic_events_calendar(limit=5)

print(f"行数: {len(df)}")
print(f"列名: {list(df.columns)}")

if len(df) > 0:
    print("\n第一行数据:")
    row = df.iloc[0]
    for col in df.columns:
        print(f"  {col}: {row[col]}")

    if 'Event' in df.columns:
        print(f"\nEvent列值: {row['Event']}")
        print(f"非空数: {df['Event'].notna().sum()}/{len(df)}")