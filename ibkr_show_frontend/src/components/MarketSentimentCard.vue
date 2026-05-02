<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Card from 'primevue/card'

import { fetchMarketSentiment } from '@/api/marketSentiment'
import type { MarketSentimentResponse, VixRange, FearGreedRange } from '@/api/marketSentiment'

const data = ref<MarketSentimentResponse | null>(null)
const loading = ref(true)

const todayLabel = computed(() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const wd = weekdays[d.getDay()]
  return `${y} · ${m} · ${day} / 周${wd}`
})

function vixPosition(ranges: VixRange[]): number {
  if (!ranges.length) return 0
  for (let i = 0; i < ranges.length; i++) {
    if (ranges[i].is_current) return i
  }
  return -1
}

function fgPosition(ranges: FearGreedRange[]): number {
  if (!ranges.length) return 0
  for (let i = 0; i < ranges.length; i++) {
    if (ranges[i].is_current) return i
  }
  return -1
}

function vixBarColor(r: VixRange): string {
  return r.is_current ? r.color : `${r.color}33`
}

function fgBarColor(r: FearGreedRange): string {
  return r.is_current ? r.color : `${r.color}33`
}

function strategySummary(): string {
  if (!data.value) return ''
  const vixCurrent = data.value.vix_ranges.find(r => r.is_current)
  const fgCurrent = data.value.fear_greed_ranges.find(r => r.is_current)
  if (!vixCurrent || !fgCurrent) return ''

  const vixWord = vixCurrent.sentiment === '正常区间' ? '常规定投' :
    vixCurrent.sentiment === '极度乐观' ? '谨慎追高' :
    vixCurrent.sentiment === '恐惧上升' ? '加大定投' :
    vixCurrent.sentiment === '市场恐慌' ? '加倍定投' : '大胆抄底'

  const fgWord = fgCurrent.sentiment === '中性' ? '保持节奏' :
    fgCurrent.sentiment.includes('恐惧') ? '逢低布局' :
    fgCurrent.sentiment === '贪婪' ? '控制仓位' : '部分止盈'

  return `${vixWord} · ${fgWord}`
}

function formatValue(val: number | null): string {
  if (val === null || val === undefined) return '--'
  return val.toFixed(2)
}

async function loadData(): Promise<void> {
  loading.value = true
  try {
    data.value = await fetchMarketSentiment()
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <div class="sentiment-card">
    <div class="sentiment-card__header">
      <span class="sentiment-card__badge">◆ DAILY MARKET PULSE</span>
      <span class="sentiment-card__date">{{ todayLabel }}</span>
    </div>

    <div v-if="loading" class="sentiment-card__loading">加载中...</div>
    <template v-else-if="data">
      <h3 class="sentiment-card__title">今日美股情绪观察</h3>
      <p class="sentiment-card__subtitle">
        S&P 500 · VIX & CNN FEAR & GREED &nbsp; 标普500 波动率指数 · 恐惧与贪婪指数
      </p>

      <div class="sentiment-card__grid">
        <!-- VIX -->
        <div class="sentiment-gauge sentiment-gauge--vix">
          <div class="gauge-header">
            <div class="gauge-label">
              <span class="gauge-line gauge-line--green" />
              <span>VIX · S&P 500</span>
            </div>
            <span class="gauge-sublabel">波动率指数</span>
          </div>
          <div class="gauge-body">
            <span class="gauge-value gauge-value--green">{{ formatValue(data.vix_value) }}</span>
            <span
              v-if="data.vix_level"
              class="gauge-badge gauge-badge--green"
            >{{ data.vix_level }}</span>
          </div>
          <div class="range-bar">
            <div
              v-for="(r, idx) in data.vix_ranges"
              :key="'vix-' + idx"
              class="range-segment"
              :style="{ backgroundColor: vixBarColor(r) }"
              :title="r.label + ' ' + r.sentiment"
            />
            <div
              class="range-marker"
              :style="{ left: ((vixPosition(data.vix_ranges) + 0.5) / data.vix_ranges.length * 100) + '%' }"
            >▼</div>
          </div>
          <div class="range-labels">
            <span v-for="(r, idx) in data.vix_ranges" :key="'vl-' + idx">{{ r.label }}</span>
          </div>
        </div>

        <!-- Fear & Greed -->
        <div class="sentiment-gauge sentiment-gauge--fg">
          <div class="gauge-header">
            <div class="gauge-label">
              <span class="gauge-line gauge-line--yellow" />
              <span>FEAR & GREED · CNN</span>
            </div>
            <span class="gauge-sublabel">恐惧与贪婪指数</span>
          </div>
          <div class="gauge-body">
            <span class="gauge-value gauge-value--yellow">{{ formatValue(data.fear_greed_value) }}</span>
            <span
              v-if="data.fear_greed_level"
              class="gauge-badge gauge-badge--yellow"
            >{{ data.fear_greed_level }}</span>
          </div>
          <div class="range-bar">
            <div
              v-for="(r, idx) in data.fear_greed_ranges"
              :key="'fg-' + idx"
              class="range-segment"
              :style="{ backgroundColor: fgBarColor(r) }"
              :title="r.label + ' ' + r.sentiment"
            />
            <div
              class="range-marker range-marker--yellow"
              :style="{ left: ((fgPosition(data.fear_greed_ranges) + 0.5) / data.fear_greed_ranges.length * 100) + '%' }"
            >▼</div>
          </div>
          <div class="range-labels">
            <span v-for="(r, idx) in data.fear_greed_ranges" :key="'fl-' + idx">{{ r.label }}</span>
          </div>
        </div>
      </div>

      <!-- Playbook -->
      <div class="playbook-section">
        <!-- VIX Playbook -->
        <div class="playbook playbook--vix">
          <div class="playbook-title">
            <span class="playbook-line playbook-line--green" />VIX PLAYBOOK
            <span class="playbook-desc">VIX 区间 · 市场情绪 · 定投策略</span>
          </div>
          <table class="playbook-table">
            <thead>
              <tr>
                <th>VIX 区间</th>
                <th>市场情绪</th>
                <th>定投策略</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(r, idx) in data.vix_ranges"
                :key="'vp-' + idx"
                :class="{ 'row--active': r.is_current }"
              >
                <td class="col-range" :style="{ color: r.color }">{{ r.label }}</td>
                <td>{{ r.sentiment }}</td>
                <td>{{ r.strategy }}</td>
                <td class="col-now">
                  <span v-if="r.is_current" class="now-tag now-tag--green">NOW</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- F&G Playbook -->
        <div class="playbook playbook--fg">
          <div class="playbook-title">
            <span class="playbook-line playbook-line--yellow" />FEAR & GREED PLAYBOOK
            <span class="playbook-desc">指数区间 · 市场情绪 · 定投策略</span>
          </div>
          <table class="playbook-table">
            <thead>
              <tr>
                <th>指数区间</th>
                <th>市场情绪</th>
                <th>定投策略</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(r, idx) in data.fear_greed_ranges"
                :key="'fp-' + idx"
                :class="{ 'row--active': r.is_current }"
              >
                <td class="col-range" :style="{ color: r.color }">{{ r.label }}</td>
                <td>{{ r.sentiment }}</td>
                <td>{{ r.strategy }}</td>
                <td class="col-now">
                  <span v-if="r.is_current" class="now-tag now-tag--yellow">NOW</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Strategy Summary -->
      <div v-if="strategySummary()" class="strategy-summary">
        <span class="strategy-diamond">◆</span>TODAY'S STRATEGY · 今日策略
        <strong>{{ strategySummary() }}</strong>
      </div>
    </template>

    <div v-else class="sentiment-card__error">暂无市场情绪数据</div>
  </div>
</template>

<style scoped>
.sentiment-card {
  background: rgba(10, 18, 32, 0.6);
  border: 1px solid rgba(129, 160, 207, 0.12);
  border-radius: 14px;
  padding: var(--space-5);
}

.sentiment-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.sentiment-card__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 14px;
  border-radius: 20px;
  background: #1a2332;
  color: var(--color-text-secondary);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.sentiment-card__date {
  color: var(--color-text-secondary);
  font-size: 0.82rem;
  font-weight: 600;
}

.sentiment-card__title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.sentiment-card__subtitle {
  font-size: 0.85rem;
  color: var(--color-accent-strong);
  margin-bottom: var(--space-5);
  letter-spacing: 0.02em;
}

.sentiment-card__loading,
.sentiment-card__error {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

/* Grid */
.sentiment-card__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

@media (max-width: 700px) {
  .sentiment-card__grid {
    grid-template-columns: 1fr;
  }
}

/* Gauge */
.sentiment-gauge {
  background: rgba(10, 18, 32, 0.5);
  border: 1px solid rgba(129, 160, 207, 0.1);
  border-radius: 12px;
  padding: var(--space-4);
}

.gauge-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-2);
}

.gauge-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--color-text-primary);
}

.gauge-line {
  display: inline-block;
  width: 24px;
  height: 3px;
  border-radius: 2px;
}
.gauge-line--green { background: #22c55e; }
.gauge-line--yellow { background: #eab308; }

.gauge-sublabel {
  font-size: 0.78rem;
  color: var(--color-text-secondary);
}

.gauge-body {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.gauge-value {
  font-size: 3.2rem;
  font-weight: 900;
  line-height: 1;
}
.gauge-value--green { color: #22c55e; }
.gauge-value--yellow { color: #eab308; }

.gauge-badge {
  display: inline-block;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}
.gauge-badge--green {
  border: 1.5px solid rgba(34, 197, 94, 0.45);
  color: #22c55e;
  background: rgba(34, 197, 94, 0.08);
}
.gauge-badge--yellow {
  border: 1.5px solid rgba(234, 179, 8, 0.45);
  color: #eab308;
  background: rgba(234, 179, 8, 0.08);
}

/* Range Bar */
.range-bar {
  position: relative;
  display: flex;
  height: 14px;
  border-radius: 7px;
  overflow: visible;
  margin-bottom: 6px;
}

.range-segment {
  flex: 1;
  transition: opacity 0.2s;
}

.range-marker {
  position: absolute;
  top: 14px;
  transform: translateX(-50%);
  font-size: 11px;
  color: var(--color-text-primary);
  z-index: 1;
}
.range-marker--yellow { color: #eab308; }

.range-labels {
  display: flex;
  font-size: 0.72rem;
  color: var(--color-text-tertiary);
}
.range-labels span {
  flex: 1;
  text-align: center;
}

/* Playbook */
.playbook-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

@media (max-width: 900px) {
  .playbook-section {
    grid-template-columns: 1fr;
  }
}

.playbook {
  background: rgba(10, 18, 32, 0.35);
  border: 1px solid rgba(129, 160, 207, 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.playbook-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: var(--space-3) var(--space-4);
  font-weight: 800;
  font-size: 0.88rem;
  color: var(--color-text-primary);
  letter-spacing: 0.04em;
}

.playbook-line {
  display: inline-block;
  width: 20px;
  height: 3px;
  border-radius: 2px;
}
.playbook-line--green { background: #22c55e; }
.playbook-line--yellow { background: #eab308; }

.playbook-desc {
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.playbook-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.playbook-table th,
.playbook-table td {
  padding: 7px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(129, 160, 207, 0.06);
}

.playbook-table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.76rem;
  background: rgba(10, 18, 32, 0.4);
}

.playbook-table tbody tr:hover {
  background: rgba(86, 213, 255, 0.04);
}

.row--active {
  background: rgba(34, 197, 94, 0.06) !important;
}

.col-range {
  font-weight: 700;
  font-family: monospace;
  white-space: nowrap;
}

.col-now {
  width: 52px;
  text-align: center;
}

.now-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.05em;
}
.now-tag--green {
  background: #22c55e;
  color: #052e16;
}
.now-tag--yellow {
  background: #eab308;
  color: #4a3800;
}

/* Strategy Summary */
.strategy-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--space-3) var(--space-4);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 10px;
  background: rgba(34, 197, 94, 0.06);
  font-size: 0.92rem;
  color: var(--color-text-secondary);
}

.strategy-diamond {
  color: #22c55e;
  font-size: 0.75rem;
}

.strategy-summary strong {
  color: var(--color-text-primary);
  margin-left: auto;
  font-weight: 700;
}
</style>
