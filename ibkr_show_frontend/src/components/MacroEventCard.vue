<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Card from 'primevue/card'

import { fetchMacroEvents } from '@/api/financialCalendar'
import type { MacroEvent } from '@/api/financialCalendar'

const props = defineProps<{
  startDate: string
  endDate: string
}>()

const emit = defineEmits<{
  refresh: []
}>()

const events = ref<MacroEvent[]>([])
const loading = ref(true)
const errorMessage = ref('')

const eventTypeConfig: Record<string, { icon: string; color: string; label: string }> = {
  nfp: { icon: '📊', color: 'var(--primitive-color-blue-400)', label: '非农' },
  cpi: { icon: '📈', color: 'var(--primitive-color-orange-400)', label: 'CPI' },
  fomc: { icon: '🏦', color: 'var(--primitive-color-red-400)', label: 'FOMC' },
  gdp: { icon: '📉', color: 'var(--primitive-color-green-400)', label: 'GDP' },
  ppi: { icon: '🏭', color: 'var(--primitive-color-purple-400)', label: 'PPI' },
  unemployment: { icon: '👥', color: 'var(--primitive-color-yellow-400)', label: '失业率' },
  retail_sales: { icon: '🛒', color: 'var(--primitive-color-teal-400)', label: '零售' },
  other: { icon: '📌', color: 'var(--color-text-secondary)', label: '其他' },
}

const highImportanceEvents = computed(() =>
  events.value.filter(e => e.importance === 'high'),
)

const mediumImportanceEvents = computed(() =>
  events.value.filter(e => e.importance === 'medium'),
)

function getTypeConfig(type: string) {
  return eventTypeConfig[type] || eventTypeConfig.other
}

function formatEventTime(event: MacroEvent): string {
  if (!event.time) return '--'
  return `ET ${event.time}`
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const wd = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return `${m}/${day} (周${wd})`
}

const countByType = computed(() => {
  const counts: Record<string, number> = {}
  for (const evt of events.value) {
    counts[evt.type] = (counts[evt.type] || 0) + 1
  }
  return counts
})

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await fetchMacroEvents(props.startDate, props.endDate)
    events.value = res.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载宏观事件失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <Card class="macro-card surface-panel">
    <template #content>
      <div class="surface-panel__content">
        <div class="macro-card__header">
          <div>
            <p class="eyebrow">Macro Calendar</p>
            <h2 class="panel-title macro-card__title">宏观事件日历</h2>
            <p class="panel-subtitle macro-card__subtitle">
              美国重要经济数据发布与 FOMC 议息会议时间表
            </p>
          </div>
        </div>

        <LoadingBlock v-if="loading" />
        <ErrorBlock v-else-if="errorMessage" :message="errorMessage" />

        <template v-else>
          <!-- Summary badges -->
          <div v-if="Object.keys(countByType).length" class="macro-card__summary">
            <span
              v-for="(count, type) in countByType"
              :key="type"
              class="macro-type-badge"
              :style="{ borderColor: getTypeConfig(type).color, color: getTypeConfig(type).color }"
            >
              {{ getTypeConfig(type).label }}
              <span class="macro-type-count">{{ count }}</span>
            </span>
          </div>

          <!-- High importance events -->
          <div v-if="highImportanceEvents.length" class="macro-card__section">
            <h3 class="macro-card__section-title">
              <span class="importance-dot importance-dot--high" />
              重点关注
            </h3>
            <div class="macro-event-list">
              <div
                v-for="(evt, idx) in highImportanceEvents"
                :key="'high-' + idx"
                class="macro-event-row macro-event-row--high"
              >
                <div class="macro-event__icon" :style="{ backgroundColor: getTypeConfig(evt.type).color + '20' }">
                  <span>{{ getTypeConfig(evt.type).icon }}</span>
                </div>
                <div class="macro-event__info">
                  <div class="macro-event__title">
                    <span class="macro-event__type-tag" :style="{ backgroundColor: getTypeConfig(evt.type).color + '15', color: getTypeConfig(evt.type).color }">
                      {{ getTypeConfig(evt.type).label }}
                    </span>
                    {{ evt.title }}
                  </div>
                  <div class="macro-event__desc">{{ evt.description }}</div>
                </div>
                <div class="macro-event__meta">
                  <div class="macro-event__date">{{ formatDate(evt.date) }}</div>
                  <div class="macro-event__time">{{ formatEventTime(evt) }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Medium/Low importance events -->
          <div v-if="mediumImportanceEvents.length" class="macro-card__section">
            <h3 class="macro-card__section-title">
              <span class="importance-dot importance-dot--medium" />
              其他经济数据
            </h3>
            <div class="macro-event-list">
              <div
                v-for="(evt, idx) in mediumImportanceEvents"
                :key="'med-' + idx"
                class="macro-event-row macro-event-row--medium"
              >
                <div class="macro-event__icon" :style="{ backgroundColor: getTypeConfig(evt.type).color + '20' }">
                  <span>{{ getTypeConfig(evt.type).icon }}</span>
                </div>
                <div class="macro-event__info">
                  <div class="macro-event__title">
                    <span class="macro-event__type-tag" :style="{ backgroundColor: getTypeConfig(evt.type).color + '15', color: getTypeConfig(evt.type).color }">
                      {{ getTypeConfig(evt.type).label }}
                    </span>
                    {{ evt.title }}
                  </div>
                  <div class="macro-event__desc">{{ evt.description }}</div>
                </div>
                <div class="macro-event__meta">
                  <div class="macro-event__date">{{ formatDate(evt.date) }}</div>
                  <div class="macro-event__time">{{ formatEventTime(evt) }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="events.length === 0" class="empty-state">
            当前时段无宏观事件
          </div>

          <p class="macro-card__footnote">
            共 {{ events.length }} 项宏观事件 · 数据以美国东部时间(ET)为准
          </p>
        </template>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.macro-card__header {
  margin-bottom: var(--space-4);
}

.macro-card__title {
  margin-bottom: 0;
}

.macro-card__subtitle {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  margin-top: var(--space-1);
}

/* Summary badges */
.macro-card__summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.macro-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 600;
  background: var(--color-surface);
}

.macro-type-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  border-radius: 10px;
  background: currentColor;
  color: var(--color-surface);
  font-size: 0.75rem;
  padding: 0 5px;
}

/* Sections */
.macro-card__section {
  margin-bottom: var(--space-4);
}

.macro-card__section:last-child {
  margin-bottom: 0;
}

.macro-card__section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.importance-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.importance-dot--high {
  background: var(--primitive-color-red-400);
}

.importance-dot--medium {
  background: var(--primitive-color-yellow-400);
}

/* Event list */
.macro-event-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.macro-event-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: 8px;
  background: var(--color-surface);
  transition: background 0.15s ease;
}

.macro-event-row:hover {
  background: var(--color-surface-hover);
}

.macro-event-row--high {
  border-left: 3px solid var(--primitive-color-red-400);
}

.macro-event-row--medium {
  border-left: 3px solid var(--primitive-color-yellow-400);
}

.macro-event__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 1rem;
  flex-shrink: 0;
}

.macro-event__info {
  flex: 1;
  min-width: 0;
}

.macro-event__title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.macro-event__type-tag {
  display: inline-flex;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  flex-shrink: 0;
}

.macro-event__desc {
  font-size: 0.82rem;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.macro-event__meta {
  text-align: right;
  flex-shrink: 0;
}

.macro-event__date {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
}

.macro-event__time {
  font-size: 0.78rem;
  color: var(--color-text-secondary);
  margin-top: 1px;
}

.macro-card__footnote {
  font-size: 0.82rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-3);
  text-align: right;
}
</style>