# ibkr_show_frontend

Vue 3 + Vite + TypeScript 前端查询层，当前提供四个页面：

- `/`：Dashboard，展示账户总览和权益曲线
- `/positions`：持仓列表，支持筛选、排序、分页
- `/trades`：交易记录和交易汇总，支持筛选、排序、分页
- `/cash-flows`：出入金记录，支持筛选、排序、分页

## 安装依赖

```bash
cd /path/to/ibkr_show/ibkr_show_frontend
npm install
```

## 启动开发环境

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

## 与后端联调

- 前端默认请求 `http://localhost:8000`
- 需要先启动 backend：

```bash
cd /path/to/ibkr_show/ibkr_show_backend
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果后端或 ES 不可达，页面会显示错误提示，不会静默失败。
