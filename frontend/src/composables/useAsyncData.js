import { ref } from 'vue'
import { extractError } from '@/services/api'

export function useAsyncData(fetcher) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function load(...args) {
    loading.value = true
    error.value = null
    try {
      data.value = await fetcher(...args)
      return data.value
    } catch (err) {
      error.value = extractError(err)
      data.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, load }
}
