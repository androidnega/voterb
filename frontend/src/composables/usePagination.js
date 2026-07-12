import { ref, computed, watch } from 'vue'

export function usePagination(source, pageSize = 10) {
  const page = ref(1)
  const size = ref(pageSize)

  const total = computed(() => (Array.isArray(source.value) ? source.value.length : 0))
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size.value) || 1))

  const paginated = computed(() => {
    const items = Array.isArray(source.value) ? source.value : []
    const start = (page.value - 1) * size.value
    return items.slice(start, start + size.value)
  })

  const from = computed(() => (total.value === 0 ? 0 : (page.value - 1) * size.value + 1))
  const to = computed(() => Math.min(page.value * size.value, total.value))

  watch(total, () => {
    if (page.value > totalPages.value) page.value = totalPages.value
  })

  watch(source, () => {
    page.value = 1
  })

  const setPage = (nextPage) => {
    page.value = Math.min(Math.max(1, nextPage), totalPages.value)
  }

  const setPageSize = (nextSize) => {
    size.value = nextSize
    page.value = 1
  }

  return {
    page,
    size,
    total,
    totalPages,
    paginated,
    from,
    to,
    setPage,
    setPageSize,
    reset: () => { page.value = 1 },
  }
}
