import { ref } from 'vue'

const loading = ref(false)

export function useLoading() {
  const start = () => { loading.value = true }
  const done = () => { loading.value = false }
  return { loading, start, done }
}
