import requests
import json
import re
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.cnn.com/markets/fear-and-greed"
}

print("=" * 60)
print("测试 CNN Fear & Greed 数据获取")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 测试 1: CNN Money 页面
print("\n[1] 测试 CNN Money API...")
try:
    resp = requests.get("https://money.cnn.com/data/fear-and-greed/", headers=headers, timeout=15)
    print(f"    状态码: {resp.status_code}")
    
    if resp.status_code == 200:
        content = resp.text
        print(f"    页面大小: {len(content)} 字符")
        
        # 查找 JSON 数据模式
        patterns = [
            (r'"fear_and_greed"\s*:\s*({.*?})', "fear_and_greed JSON"),
            (r'var\s+fearGreedData\s*=\s*(.*?);', "JavaScript 变量"),
            (r'(\{[^{}]*"value"[^{}]*\})', "value 字段"),
        ]
        
        found_data = False
        for pattern, desc in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                print(f"    ✅ 找到 {desc}: {len(matches)} 个匹配")
                for i, match in enumerate(matches[:2]):
                    print(f"       [{i+1}] {match[:150]}...")
                found_data = True
                break
        
        if not found_data:
            # 查找数字（可能是指数值）
            numbers = re.findall(r'\b(?:Fear & Greed|Current)\b.*?(\d+)', content, re.IGNORECASE)
            if numbers:
                print(f"    ⚠️  找到数字引用: {numbers[:3]}")
            
            # 显示部分 HTML 内容
            if "fear" in content.lower():
                idx = content.lower().find("fear")
                snippet = content[max(0,idx-100):idx+200]
                print(f"    📄 HTML 片段:\n{snippet}")
            else:
                print(f"    ❌ 未找到 fear 相关内容")
    else:
        print(f"    ❌ HTTP 错误: {resp.status_code}")

except Exception as e:
    print(f"    ❌ 异常: {e}")

# 测试 2: 尝试直接找 API 端点
print("\n[2] 尝试常见 API 端点...")
api_endpoints = [
    "https://money.cnn.com/data/fear-and-greed/?format=json",
    "https://data.cnbc.com/json/fear-greed",
]

for url in api_endpoints:
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200 and len(resp.text) > 50:
            data = resp.json()
            print(f"    ✅ {url.split('/')[-2]}")
            print(f"       数据: {json.dumps(data, indent=2)[:200]}")
            break
    except:
        pass

# 测试 3: 使用 BeautifulSoup 解析（如果可用）
print("\n[3] 尝试解析页面结构...")
try:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 查找包含指数值的元素
    elements = soup.find_all(text=re.compile(r'\d+', re.I))
    for elem in elements[:5]:
        parent = elem.parent
        if parent and ('class' in parent.attrs or 'id' in parent.attrs):
            text = elem.strip()
            if text.isdigit() and 0 <= int(text) <= 100:
                print(f"    ✅ 找到可能的指数值: {text} (在 {parent.name}.{parent.get('class', [])})")
                
except ImportError:
    print("    ⚠️  BeautifulSoup 未安装，跳过详细解析")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)