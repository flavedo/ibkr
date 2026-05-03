<script setup lang="ts">
import Card from 'primevue/card'

defineProps<{
  title: string
  value: string
  helper?: string
  tone?: 'neutral' | 'positive' | 'negative' | 'accent'
  icon?: string
  deltaAmount?: string
  deltaPercent?: string
  deltaTone?: 'neutral' | 'positive' | 'negative' | 'accent'
}>()
</script>

<template>
  <Card class="stat-card" :class="tone ? `stat-card--${tone}` : 'stat-card--neutral'">
    <template #content>
      <div class="stat-card__row">
        <div
          v-if="deltaAmount || deltaPercent"
          class="stat-card__delta"
          :class="deltaTone ? `stat-card__delta--${deltaTone}` : 'stat-card__delta--neutral'"
        >
          <span v-if="deltaPercent" class="stat-card__delta-line">{{ deltaPercent }}</span>
          <span v-if="deltaAmount" class="stat-card__delta-line">{{ deltaAmount }}</span>
        </div>
        <div v-if="icon" class="stat-card__icon">
          <i :class="icon"></i>
        </div>
        <div class="stat-card__content">
          <p class="stat-card__title">{{ title }}</p>
          <p class="stat-card__value">{{ value }}</p>
          <p class="stat-card__helper">{{ helper || '\u00A0' }}</p>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.stat-card {
  min-height: 96px;
  transition: transform 200ms ease, box-shadow 200ms ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(2, 10, 24, 0.3);
  }
}

.stat-card__row {
  position: relative;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.stat-card__delta {
  position: absolute;
  top: 4px;
  right: 4px;
  display: grid;
  justify-items: end;
  gap: 1px;
  font-size: 0.72rem;
  line-height: 1.1;
  color: var(--color-text-secondary);
}

.stat-card__delta-line {
  white-space: nowrap;
}

.stat-card__icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  border: 1px solid rgba(86, 213, 255, 0.16);
  background: rgba(10, 38, 57, 0.36);
}

.stat-card__icon i {
  color: var(--color-accent-strong);
  font-size: 1rem;
}

.stat-card__content {
  display: grid;
  align-content: start;
  min-width: 0;
  padding-top: 2px;
}

.stat-card__title,
.stat-card__helper {
  margin: 0;
  color: var(--color-text-secondary);
}

.stat-card__value {
  margin: 0.25rem 0 0;
  font-size: clamp(1.25rem, 2.2vw, 1.65rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
  white-space: nowrap;
}

.stat-card__helper {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  min-height: 0.9rem;
  opacity: 0.85;
}

.stat-card--positive .stat-card__value {
  color: var(--color-positive);
}

.stat-card--negative .stat-card__value {
  color: var(--color-negative);
}

.stat-card--accent .stat-card__value {
  color: var(--color-accent-strong);
}

.stat-card--positive .stat-card__icon {
  border-color: rgba(52, 210, 163, 0.18);
  background: rgba(9, 47, 39, 0.34);
}

.stat-card--negative .stat-card__icon {
  border-color: rgba(255, 107, 125, 0.18);
  background: rgba(55, 18, 28, 0.3);
}

.stat-card--negative .stat-card__icon i {
  color: var(--color-negative);
}

.stat-card--positive .stat-card__icon i {
  color: var(--color-positive);
}

.stat-card__delta--positive {
  color: var(--color-positive);
}

.stat-card__delta--negative {
  color: var(--color-negative);
}

.stat-card__delta--accent {
  color: var(--color-accent-strong);
}
</style>
