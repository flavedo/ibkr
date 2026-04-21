<script setup lang="ts">
import { computed, ref } from 'vue'
import Card from 'primevue/card'

export interface PieSegmentItem {
  label: string
  value: number
  color: string
  note?: string
  members?: string[]
}

const props = defineProps<{
  title: string
  subtitle: string
  items: PieSegmentItem[]
  formatNumber: (value: number | null, digits?: number) => string
}>()

const chartSize = 220
const strokeWidth = 30
const radius = (chartSize - strokeWidth) / 2
const circumference = 2 * Math.PI * radius
const hoveredItem = ref<PieSegmentItem | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })
const contentRef = ref<HTMLElement | null>(null)

const total = computed(() => props.items.reduce((sum, item) => sum + item.value, 0))

const chartSegments = computed(() => {
  if (total.value <= 0) {
    return []
  }

  let currentOffset = 0

  return props.items
    .filter((item) => item.value > 0)
    .map((item) => {
      const ratio = item.value / total.value
      const length = ratio * circumference
      const segment = {
        ...item,
        ratio,
        dashArray: `${length} ${circumference - length}`,
        dashOffset: -currentOffset,
      }
      currentOffset += length
      return segment
    })
})

function percentage(value: number): string {
  if (total.value <= 0) {
    return '0.0%'
  }
  return `${((value / total.value) * 100).toFixed(1)}%`
}

function membersText(item: PieSegmentItem): string {
  if (!item.members || item.members.length === 0) {
    return '暂无明细'
  }

  return item.members.join('、')
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function showTooltip(item: PieSegmentItem, event: MouseEvent): void {
  const contentRect = contentRef.value?.getBoundingClientRect()
  const tooltipWidth = 320
  const tooltipHeight = 140
  const padding = 16

  hoveredItem.value = item
  if (!contentRect) {
    tooltipPosition.value = { x: 24, y: 24 }
    return
  }

  const rawX = event.clientX - contentRect.left + 18
  const rawY = event.clientY - contentRect.top + 18

  tooltipPosition.value = {
    x: clamp(rawX, padding, contentRect.width - tooltipWidth - padding),
    y: clamp(rawY, padding, contentRect.height - tooltipHeight - padding),
  }
}

function hideTooltip(): void {
  hoveredItem.value = null
}
</script>

<template>
  <Card class="distribution-card surface-panel">
    <template #content>
      <div ref="contentRef" class="surface-panel__content distribution-card__content">
        <div>
          <h4 class="distribution-card__title">{{ title }}</h4>
          <p class="distribution-card__subtitle">{{ subtitle }}</p>
        </div>

        <div v-if="chartSegments.length === 0" class="empty-state distribution-card__empty">
          当前条件下暂无可绘制数据
        </div>

        <div v-else class="distribution-card__layout">
          <div class="distribution-card__chart-shell">
            <svg :viewBox="`0 0 ${chartSize} ${chartSize}`" class="distribution-card__chart" aria-label="pie chart">
              <circle
                :cx="chartSize / 2"
                :cy="chartSize / 2"
                :r="radius"
                class="distribution-card__track"
              />
              <circle
                v-for="item in chartSegments"
                :key="item.label"
                :cx="chartSize / 2"
                :cy="chartSize / 2"
                :r="radius"
                :stroke="item.color"
                :stroke-dasharray="item.dashArray"
                :stroke-dashoffset="item.dashOffset"
                class="distribution-card__segment"
                @mouseenter="showTooltip(item, $event)"
                @mousemove="showTooltip(item, $event)"
                @mouseleave="hideTooltip"
              />
            </svg>
            <div class="distribution-card__center">
              <span>总规模</span>
              <strong>{{ formatNumber(total, 2) }}</strong>
            </div>
          </div>

          <div class="distribution-card__legend">
            <div v-for="item in chartSegments" :key="item.label" class="distribution-card__legend-row">
              <div
                class="distribution-card__legend-main"
                @mouseenter="showTooltip(item, $event)"
                @mousemove="showTooltip(item, $event)"
                @mouseleave="hideTooltip"
              >
                <span class="distribution-card__swatch" :style="{ backgroundColor: item.color }"></span>
                <div>
                  <div class="distribution-card__legend-head">
                    <strong>{{ item.label }}</strong>
                    <em>{{ percentage(item.value) }}</em>
                  </div>
                  <p>{{ item.note || '分类说明' }}</p>
                  <small>包含：{{ membersText(item) }}</small>
                </div>
              </div>
              <strong>{{ formatNumber(item.value, 2) }}</strong>
            </div>
          </div>
        </div>

        <div
          v-if="hoveredItem"
          class="distribution-card__tooltip"
          :style="{ left: `${tooltipPosition.x}px`, top: `${tooltipPosition.y}px` }"
        >
          <strong>{{ hoveredItem.label }}</strong>
          <span>{{ formatNumber(hoveredItem.value, 2) }} · {{ percentage(hoveredItem.value) }}</span>
          <p>{{ hoveredItem.note || '分类说明' }}</p>
          <small>包含：{{ membersText(hoveredItem) }}</small>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.distribution-card {
  height: 100%;
  overflow: visible;
  z-index: 3;
}

.distribution-card__content {
  display: grid;
  gap: var(--space-4);
  height: 100%;
  overflow: visible;
}

.distribution-card__title {
  margin: 0;
  font-size: 1rem;
}

.distribution-card__subtitle {
  margin: 0.45rem 0 0;
  color: var(--color-text-secondary);
  font-size: 0.92rem;
}

.distribution-card__layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
  align-items: start;
}

.distribution-card__chart-shell {
  position: relative;
  width: 240px;
  height: 240px;
  justify-self: center;
  overflow: visible;
}

.distribution-card__chart {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.distribution-card__track,
.distribution-card__segment {
  fill: none;
  stroke-width: 30;
}

.distribution-card__track {
  stroke: rgba(129, 160, 207, 0.12);
}

.distribution-card__segment {
  stroke-linecap: butt;
}

.distribution-card__center {
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%);
  display: grid;
  gap: 4px;
  text-align: center;
}

.distribution-card__center span {
  color: var(--color-text-secondary);
  font-size: 0.82rem;
}

.distribution-card__center strong {
  font-size: 1.05rem;
}

.distribution-card__legend {
  display: grid;
  gap: 12px;
  align-content: start;
}

.distribution-card__legend-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-4);
  align-items: start;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(129, 160, 207, 0.1);
  background: rgba(15, 26, 45, 0.72);
}

.distribution-card__legend-main {
  display: flex;
  gap: 12px;
  min-width: 0;
  align-items: flex-start;
}

.distribution-card__legend-main p {
  margin: 0.2rem 0 0;
  color: var(--color-text-secondary);
  font-size: 0.86rem;
}

.distribution-card__legend-main small {
  display: block;
  margin-top: 0.35rem;
  color: rgba(194, 207, 232, 0.9);
  font-size: 0.82rem;
  line-height: 1.55;
  white-space: normal;
  word-break: break-word;
}

.distribution-card__legend-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.distribution-card__legend-head em {
  color: var(--color-accent-strong);
  font-style: normal;
  font-size: 0.86rem;
}

.distribution-card__legend-main strong,
.distribution-card__legend-row > strong {
  font-size: 1rem;
}

.distribution-card__swatch {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  margin-top: 0.35rem;
  flex: 0 0 auto;
}

.distribution-card__tooltip {
  position: absolute;
  z-index: 12;
  pointer-events: none;
  display: grid;
  gap: 4px;
  min-width: 220px;
  max-width: 320px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(129, 160, 207, 0.18);
  background: rgba(7, 13, 24, 0.96);
  box-shadow: 0 16px 30px rgba(0, 0, 0, 0.35);
}

.distribution-card__tooltip strong {
  font-size: 0.92rem;
}

.distribution-card__tooltip span {
  color: var(--color-text-secondary);
  font-size: 0.82rem;
}

.distribution-card__tooltip p,
.distribution-card__tooltip small {
  margin: 0;
  color: rgba(210, 219, 240, 0.92);
  font-size: 0.82rem;
  line-height: 1.5;
  white-space: normal;
}

.distribution-card__empty {
  min-height: 280px;
}

@media (max-width: 1024px) {
  .distribution-card__chart-shell {
    width: 220px;
    height: 220px;
  }
}
</style>
