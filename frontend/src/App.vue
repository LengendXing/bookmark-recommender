<template>
  <component :is="layout" :sidebarOpen="sidebarOpen">
    <router-view />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AuthLayout from '@/layouts/AuthLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { ref } from 'vue'

const route = useRoute()
const sidebarOpen = ref(true)

const layout = computed(() => (route.name === 'Login' ? AuthLayout : AdminLayout))
</script>
