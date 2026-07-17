import { ref, computed, onUnmounted } from 'vue'

const headingOverride = ref(null)

/**
 * Shell header reads this. Detail pages call setPageHeading({ title, subtitle }).
 * Cleared automatically on unmount when using usePageHeading().
 */
export function usePageHeading() {
  const setPageHeading = (meta) => {
    if (!meta || !meta.title) {
      headingOverride.value = null
      return
    }
    headingOverride.value = {
      title: meta.title,
      subtitle: meta.subtitle || '',
    }
  }

  const clearPageHeading = () => {
    headingOverride.value = null
  }

  onUnmounted(clearPageHeading)

  return { setPageHeading, clearPageHeading }
}

export function useShellPageHeading(fallbackMeta) {
  return computed(() => {
    if (headingOverride.value?.title) {
      return {
        title: headingOverride.value.title,
        subtitle: headingOverride.value.subtitle || fallbackMeta.value?.subtitle || '',
      }
    }
    return fallbackMeta.value
  })
}
