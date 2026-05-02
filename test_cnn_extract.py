import requests
import re
import json
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.cnn.com/markets/fear-and-greed"
}

print("=" * 60)
print("提取 CNN Fear & Greed 核心数据")
print("=" * 60)

resp = requests.get("https://money.cnn.com/data/fear-and-greed/", headers=headers, timeout=20)
content = resp.text

# 提取所有 script 标签
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)

print(f"\n找到 {len(scripts)} 个 script 标签\n")

# 分析 Script #2 (包含 fear/greed 数据)
for i, script in enumerate(scripts):
    if 'fear' in script.lower() or 'greed' in script.lower():
        if len(script) < 20000:  # 只处理较小的脚本
            print(f"{'='*60}")
            print(f"Script #{i+1} (长度: {len(script):,})")
            print(f"{'='*60}\n")
            
            # 尝试找 JSON 对象或变量赋值
            patterns_to_try = [
                r'var\s+(\w+)\s*=\s*(\{.*?\});',
                r'(?:window|global)\.(\w+)\s*=\s*(\{.*?\})',
                r'(\{[^{}]*(?:"fear"|"greed"|"value"|"score")[^{}]*\})',
            ]
            
            for pattern in patterns_to_try:
                matches = re.findall(pattern, script, re.DOTALL)
                if matches:
                    for match in matches:
                        var_name = match[0] if isinstance(match, tuple) and len(match) > 1 else "unknown"
                        data_str = match[-1]
                        
                        try:
                            data = json.loads(data_str)
                            print(f"✅ 找到 JSON 数据 (变量: {var_name}):")
                            print(json.dumps(data, indent=2)[:1000])
                            print("\n")
                            
                            # 如果找到了完整的 F&G 数据，就保存下来
                            if 'value' in str(data).lower() or 'fear' in str(data).lower():
                                with open('cnn_fng_data.json', 'w') as f:
                                    json.dump(data, f, indent=2)
                                print("💾 已保存到 cnn_fng_data.json")
                                
                        except json.JSONDecodeError:
                            pass
            
            # 如果没找到 JSON，显示原始内容的关键部分
            print("📄 脚本关键内容:")
            lines = [l.strip() for l in script.split('\n') if l.strip()]
            for line in lines[:30]:
                if any(kw in line.lower() for kw in ['fear', 'greed', 'value', 'index', 'data']):
                    print(f"   {line}")
            print("\n")

print("\n" + "=" * 60)
print("完成")
print("=" * 60)