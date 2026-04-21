<script setup lang="ts">
import Message from 'primevue/message'

defineProps<{ message: string }>()
</script>

<template>
  <Message severity="error" icon="pi pi-exclamation-triangle">
    {{ message }}
  </Message>
</template>
