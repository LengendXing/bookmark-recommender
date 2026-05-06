<template>
  <div class="space-y-2">
    <SkeletonBox width="100%" height="38px" />
    <SkeletonBox v-for="i in rows" :key="i" width="100%" height="48px" />
  </div>
</template>

<script setup lang="ts">
import SkeletonBox from './SkeletonBox.vue'

defineProps<{ rows?: number }>()
</script>
