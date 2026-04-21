# ibkr_show_backend

FastAPI 查询层，从 Elasticsearch 读取 IBKR ETL 数据并对前端提供 REST API。

## 快速开始

```bash
cd /path/to/ibkr_show/ibkr_show_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## ES 配置

`.env` 至少需要配置：

- `ES_HOST=http://localhost:9200`
- `CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
- `CORS_ALLOW_ORIGIN_REGEX=https?://.*`
- `ES_USERNAME=`
- `ES_PASSWORD=`
- `ES_VERIFY_CERTS=false`
- `ES_ACCOUNT_INDEX=ibkr_account_daily_snapshot_v1`
- `ES_POSITION_INDEX=ibkr_position_daily_snapshot_v1`
- `ES_TRADE_INDEX=ibkr_trade_records_v1`
- `ES_CASH_FLOW_INDEX=ibkr_cash_flow_records_v1`
- `ES_PRICE_HISTORY_INDEX=ibkr_symbol_price_history_v1`

## 启动 API

```bash
cd /path/to/ibkr_show/ibkr_show_backend
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 接口说明

- `GET /health`
- `GET /api/account/overview`
- `GET /api/account/latest-report-date`
- `GET /api/charts/equity-curve`
- `GET /api/positions`
- `GET /api/positions/detail`
- `GET /api/trades`
- `GET /api/trades/summary`
- `GET /api/cash-flows`
- `GET /api/cash-flows/summary`

## 接口示例

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/account/overview
curl 'http://localhost:8000/api/charts/equity-curve?start_date=2026-01-01&end_date=2026-04-17'
curl 'http://localhost:8000/api/positions?sort_by=position_value&sort_order=desc&page=1&page_size=20'
curl 'http://localhost:8000/api/positions/detail?symbol=AAPL&asset_class=STK'
curl 'http://localhost:8000/api/trades?sort_by=date_time&sort_order=desc&page=1&page_size=20'
curl 'http://localhost:8000/api/trades/summary?start_date=2026-01-01&end_date=2026-04-17'
curl 'http://localhost:8000/api/cash-flows?page=1&page_size=20'
curl 'http://localhost:8000/api/cash-flows/summary'
```

如果 ES 不可达或索引不存在，接口会返回清晰错误，不会把 ES 原始响应直接透传给前端。
