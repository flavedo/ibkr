# 经济日历 API 可行性测试

测试日期: 2026-04-29

## 测试结果汇总

| 方案 | 费用 | API Key | 测试结果 | 覆盖范围 | 适用性 |
|------|------|---------|---------|---------|-------|
| **[#1] yfinance Calendars** | 免费 | 不需要 | ✅ 通过 | 经济事件 / 财报 / IPO / 拆分 | ⭐ 推荐 |
| **[#2] FRED API** | 免费 | 需要 | ⏳ 待Key | 仅美国经济数据发布 | 仅用于美国数据 |
| **[#3] jblanked Forex Factory** | 免费 | 不需要 | ❌ 超时 | 全球宏观经济 | 网络不可达 |
| **[#4] Alpha Vantage** | 免费(25次/天) | 需要 | ❌ 不适合 | 经济指标历史值，无日历 | 不适合 |
| **[#5] Investing.com** | 免费 | 不需要 | ⚠️ Cloudflare | 全球宏观经济 | 爬虫不稳定 |
| **[#6] EastMoney(东方财富)** | 免费 | 不需要 | ⚠️ 需逆向API | 全球宏观经济 | 中文数据源 |

## 详细结果

### ✅ #1 yfinance Calendars — 推荐

yfinance 1.3.0 新增 `Calendars` 类，提供四个日历：

| 日历 | 方法 | 数据量 | 字段 |
|------|------|--------|------|
| 经济事件 | `get_economic_events_calendar()` | 12条/月 | Region, Event Time, For, Actual, Expected, Last, Revised |
| 财报 | `get_earnings_calendar()` | 12条 | Company, Marketcap, Event Name, Date, EPS Estimate, etc. |
| IPO | `get_ipo_info_calendar()` | 6条 | Company, Exchange, Price, Shares, etc. |
| 拆分 | `get_splits_calendar()` | 12条 | Company, Payable On, Share Worth |

**优点**: 免费、无需 API Key、直接 Python 包、覆盖 Earnings 很完整
**局限**: 经济事件以非美/发展中市场为主（泰国、科威特等），不含 impact 等级
**适合场景**: Earnings 日历 + 基础经济日历

安装: `pip install yfinance`
使用:
```python
import yfinance as yf
cal = yf.Calendars(start="2026-04-01", end="2026-06-01")
eco = cal.get_economic_events_calendar()  # 经济事件
earn = cal.get_earnings_calendar()        # 财报
```

### ⏳ #2 FRED API — 美国经济数据专用

- 端点: `https://api.stlouisfed.org/fred/releases/dates`
- 需要免费 API Key（注册: https://fred.stlouisfed.org/docs/api/api_key.html）
- 仅覆盖美国经济数据发布日历
- 包含 release_id, release_name, release_date
- **不包含** consensus forecast / impact 等级

### ❌ #3 jblanked — 从当前网络不可达

- `www.jblanked.com` SSL 证书不匹配/连接超时
- 可能在某些地区/网络环境可用
- 建议自行测试: `curl https://www.jblanked.com/news/api/forex-factory/calendar/week/`

### ❌ #4 Alpha Vantage — 不适合日历场景

- 免费版每天仅 25 次请求
- 没有统一的经济日历 API
- 只有单个经济指标的历史值查询（CPI, GDP 等）

### ⚠️ #5 Investing.com — Cloudflare 反爬

- 页面可访问（200, 1.5MB），但使用 Next.js 动态加载
- 数据通过 JavaScript 渲染，BeautifulSoup 无法直接提取
- 内部 API 端点 `ec.investing.com` DNS 不可解析
- 推荐使用第三方封装（但 jblanked 当前不可用）

### ⚠️ #6 EastMoney 东方财富 — 需逆向分析

- 页面可访问（200, 234KB）
- 数据通过 AJAX 动态加载
- 需要浏览器 DevTools 分析实际请求端点
- 数据质量好，覆盖全球 + 中国数据

## 综合推荐

### 如果以财报日历为主
👉 **yfinance Calendars** — 零成本、零配置、直接可用

### 如果需要全球经济日历 + 影响等级
建议考虑以下**付费**方案（免费方案质量有限）:

1. **Trading Economics API** — $49/试用周，最全面的经济日历
2. **EODHD Economic Calendar** — 付费，覆盖 30+ 国家
3. **RapidAPI Economic Calendar** (horizonfx) — 有免费层

### 如果需要仅美国经济数据
👉 **FRED API** — 免费权威，美国经济数据发布日历
