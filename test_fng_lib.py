from datetime import datetime
import fear_and_greed

print("测试 fear-and-greed 库")
print(f"时间: {datetime.now()}")

result = fear_and_greed.get()
print(f"结果: {result}")
print(f"值: {result.value}")
print(f"描述: {result.description}")
print(f"更新: {result.last_update}")