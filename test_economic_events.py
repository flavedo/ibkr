import sys
sys.path.insert(0, '/Volumes/Extent/Users/chengjunsen/Project/web/ibkr/ibkr_show_backend')

from datetime import datetime, timedelta
import yfinance as yf

print("=" * 60)
print("测试经济事件数据")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 使用今天和明天的日期
start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

print(f"\n查询范围: {start_date} ~ {end_date}\n")

try:
    cal = yf.Calendars(start=start_date, end=end_date)
    df = cal.get_economic_events_calendar()
    
    print(f"[1] 数据概览:")
    print(f"    行数: {len(df)}")
    print(f"    列名: {list(df.columns)}")
    
    if df.empty:
        print("\n    ❌ 没有数据!")
        exit(1)
    
    print(f"\n[2] 前 5 行数据预览:")
    print(df.head().to_string())
    
    print(f"\n[3] 检查 'Event' 列:")
    if 'Event' in df.columns:
        event_col = df['Event']
        print(f"    总行数: {len(event_col)}")
        print(f"    非空值: {event_col.notna().sum()}")
        print(f"    空值/NaN: {event_col.isna().sum()}")
        
        # 显示非空的事件名称
        non_null_events = event_col.dropna()
        if len(non_null_events) > 0:
            print(f"\n[4] 事件名称示例 (前10个):")
            for i, event in enumerate(non_null_events.head(10)):
                print(f"    [{i+1}] {event}")
        else:
            print(f"\n    ❌ 所有事件名称都为空!")
            
            # 显示其他列的内容
            print(f"\n[5] 其他列的数据:")
            for col in df.columns[:5]:
                sample = df[col].head(3).tolist()
                print(f"    {col}: {sample}")
    else:
        print(f"    ❌ 'Event' 列不存在!")
        print(f"\n    可用列: {list(df.columns)}")
        
        # 尝试找相似的列名
        similar_cols = [col for col in df.columns if 'event' in col.lower() or 'name' in col.lower()]
        if similar_cols:
            print(f"\n    相似列: {similar_cols}")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)