import requests
import json
import re
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.cnn.com/markets/fear-and-greed"
}

print("=" * 60)
print("深度测试 CNN Fear & Greed 数据")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

try:
    print("\n[1] 请求 CNN Money 页面...")
    resp = requests.get("https://money.cnn.com/data/fear-and-greed/", headers=headers, timeout=20)
    print(f"    状态码: {resp.status_code}")
    
    if resp.status_code != 200:
        print("    ❌ 请求失败")
        exit(1)
    
    content = resp.text
    print(f"    页面大小: {len(content):,} 字符")
    
    # 策略 1: 查找所有 script 标签中的 JSON 数据
    print("\n[2] 解析 Script 标签...")
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
    print(f"    找到 {len(scripts)} 个 script 标签")
    
    fng_data_found = False
    for i, script in enumerate(scripts):
        # 查找包含 fear/greed 关键词的脚本
        if 'fear' in script.lower() or 'greed' in script.lower():
            print(f"\n    ✅ Script #{i+1} 包含 fear/greed 关键词")
            print(f"       长度: {len(script):,} 字符")
            
            # 尝试提取 JSON 对象
            json_patterns = [
                r'(?:fear|greed)[^{}]*({[^{}]*(?:"value"|"score"|"rating")[^{}]*})',
                r'(\{[^{}]*"[0-9]{1,3}"[^{}]*"(?:Fear|Greed|fear|greed)"[^{}]*\})',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, script, re.DOTALL | re.IGNORECASE)
                if matches:
                    print(f"       找到 JSON 模式: {len(matches)} 个")
                    for j, match in enumerate(matches[:3]):
                        print(f"       [{j+1}] {match[:200]}")
                    fng_data_found = True
            
            if not fng_data_found and len(script) < 5000:
                print(f"       脚本内容预览:\n{script[:800]}")
    
    # 策略 2: 直接搜索数字模式 (0-100 范围的整数，可能是指数值)
    print("\n[3] 搜索可能的指数值...")
    
    # 查找 "Current" 或类似标签附近的数字
    current_patterns = [
        r'(?:Current|Latest|Index)[:\s]*(\d{1,3})',
        r'["\']?value["\']?\s*[:=]\s*["\']?(\d{1,3})',
        r'class="[^"]*(?:fear|greed|index)[^"]*"[^>]*>(\d{1,3})',
    ]
    
    for pattern_name, pattern in [("当前值", current_patterns[0]), ("JSON value", current_patterns[1]), ("HTML class", current_patterns[2])]:
        matches = re.findall(pattern, content, re.IGNORECASE)
        valid_matches = [int(m) for m in matches if 0 <= int(m) <= 100]
        if valid_matches:
            print(f"    ✅ {pattern_name}: 找到 {len(valid_matches)} 个有效值 - {valid_matches[:5]}")
    
    # 策略 3: 查找 classification 标签
    print("\n[4] 查找情绪分类...")
    classifications = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']
    for cls in classifications:
        if cls.lower() in content.lower():
            idx = content.lower().find(cls.lower())
            context = content[max(0,idx-50):idx+len(cls)+50]
            print(f"    ✅ 找到 '{cls}':")
            print(f"       上下文: ...{context}...")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)