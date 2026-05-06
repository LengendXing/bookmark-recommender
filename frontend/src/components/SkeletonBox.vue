<template>
  <div
    class="skeleton-shimmer"
    :style="{ width, height, borderRadius }"
  />
</template>

<script setup lang="ts">
defineProps<{
  width?: string
  height?: string
  borderRadius?: string
}>()
</script>
