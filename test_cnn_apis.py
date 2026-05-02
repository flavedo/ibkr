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
print("搜索 CNN Fear & Greed API 端点")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 获取页面内容并查找 API 调用
resp = requests.get("https://money.cnn.com/data/fear-and-greed/", headers=headers, timeout=20)
content = resp.text

# 提取所有 URL（可能是 API 端点）
urls_found = re.findall(r'(?:fetch|ajax|get|post|axios)\s*\(\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
api_urls = [u for u in urls_found if any(ext in u for ext in ['.json', '/api/', '/data/', '/v1/', '/v2/'])]

print(f"\n[1] 找到可能的 API 端点: {len(api_urls)} 个")
for url in api_urls[:10]:
    print(f"   • {url}")

# 尝试常见的 CNN API 模式
test_apis = [
    ("CNN Money JSON", "https://money.cnn.com/data/fear-and-greed/?format=json"),
    ("CNN Markets API v2", "https://www.cnn.com/api/v2/content/fear-and-greed"),
    ("CNN Data Feed", "https://data.cnn.com/markets/fear-and-greed"),
]

print("\n[2] 测试常见 API 端点...")
for name, url in test_apis:
    try:
        print(f"\n   测试: {name}")
        print(f"   URL: {url}")
        
        resp_api = requests.get(url, headers=headers, timeout=10)
        print(f"   状态码: {resp_api.status_code}")
        
        if resp_api.status_code == 200:
            content_type = resp_api.headers.get('Content-Type', '')
            print(f"   Content-Type: {content_type}")
            
            if 'json' in content_type:
                try:
                    data = resp_api.json()
                    print(f"   ✅ 成功获取 JSON 数据!")
                    print(f"   数据预览: {json.dumps(data, indent=2)[:500]}")
                    
                    # 保存完整数据
                    with open('cnn_fng_success.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"\n   💾 完整数据已保存到 cnn_fng_success.json")
                    
                except Exception as e:
                    print(f"   ⚠️  JSON 解析失败: {e}")
                    print(f"   原始内容前200字符: {resp_api.text[:200]}")
            else:
                if len(resp_api.text) > 100:
                    print(f"   内容长度: {len(resp_api.text)} 字符")
                    # 检查是否包含数字
                    numbers = re.findall(r'\b\d{1,3}\b', resp_api.text)
                    valid_nums = [n for n in numbers if 0 <= int(n) <= 100]
                    if valid_nums:
                        print(f"   找到可能的有效值: {valid_nums[:5]}")
        else:
            print(f"   ❌ HTTP 错误")
            
    except Exception as e:
        print(f"   ❌ 异常: {str(e)[:100]}")

# 备选方案: 使用其他免费数据源
print("\n\n[3] 测试备选数据源...")

backup_sources = [
    ("Alternative.me (当前使用)", "https://api.alternative.me/fng/?limit=1"),
    ("Finnhub", None),  # 需要API key
]

name, url = backup_sources[0]
try:
    resp_backup = requests.get(url, timeout=10)
    data = resp_backup.json()
    value = data['data'][0]['value']
    classification = data['data'][0]['value_classification']
    timestamp = datetime.fromtimestamp(int(data['data'][0]['timestamp']))
    
    print(f"\n   ✅ {name}:")
    print(f"      值: {value} ({classification})")
    print(f"      时间: {timestamp}")
    print(f"      延迟: {(datetime.now() - timestamp).total_seconds()/3600:.1f} 小时")
    
except Exception as e:
    print(f"   ❌ {name} 失败: {e}")

print("\n" + "=" * 60)