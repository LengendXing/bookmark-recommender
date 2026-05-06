<template>
  <div class="rounded-xl border border-border/50 p-5 space-y-4" style="background: hsl(var(--card))">
    <div class="flex items-center gap-3">
      <SkeletonBox width="40px" height="40px" borderRadius="8px" />
      <div class="space-y-2 flex-1">
        <SkeletonBox width="60%" height="14px" />
        <SkeletonBox width="40%" height="12px" />
      </div>
    </div>
    <div class="space-y-2">
      <SkeletonBox width="100%" height="10px" />
      <SkeletonBox width="80%" height="10px" />
    </div>
  </div>
</template>

<script setup lang="ts">
import SkeletonBox from './SkeletonBox.vue'
</script>
