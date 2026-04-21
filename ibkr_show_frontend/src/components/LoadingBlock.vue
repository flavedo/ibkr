<script setup lang="ts">
import Skeleton from 'primevue/skeleton'
</script>

<template>
  <section class="loading-block surface-panel">
    <div class="surface-panel__content loading-block__content">
      <div class="loading-block__cards">
        <Skeleton v-for="item in 4" :key="item" height="7rem" borderRadius="18px" />
      </div>
      <div class="loading-block__table">
        <Skeleton height="3rem" borderRadius="16px" />
        <Skeleton v-for="item in 5" :key="`row-${item}`" height="3.4rem" borderRadius="14px" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.loading-block__content {
  display: grid;
  gap: var(--space-4);
}

.loading-block__cards,
.loading-block__table {
  display: grid;
  gap: var(--space-3);
}

.loading-block__cards {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}
</style>
