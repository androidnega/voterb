import { defineStore } from 'pinia'
import { systemApi } from '@/api/system'

const STORAGE_KEY = 'voterb_ui_theme'
export const THEME_IDS = ['classic', 'pulse']

function isValidTheme(theme) {
  return THEME_IDS.includes(theme)
}

function applyTheme(theme) {
  const resolved = isValidTheme(theme) ? theme : 'classic'
  document.documentElement.dataset.theme = resolved
  return resolved
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: applyTheme(localStorage.getItem(STORAGE_KEY) || 'classic'),
    options: [],
    loaded: false,
    saving: false,
  }),

  getters: {
    isPulse: (state) => state.theme === 'pulse',
  },

  actions: {
    async bootstrap() {
      try {
        const { data } = await systemApi.getTheme()
        if (data?.options?.length) this.options = data.options
        if (isValidTheme(data?.theme)) {
          this.setTheme(data.theme, { persistRemote: false })
        }
      } catch {
        // Keep cached/local theme when API is unavailable
      } finally {
        this.loaded = true
      }
    },

    setTheme(theme, { persistRemote = false } = {}) {
      if (!isValidTheme(theme)) return
      this.theme = applyTheme(theme)
      localStorage.setItem(STORAGE_KEY, this.theme)
      if (persistRemote) return this.saveTheme()
      return Promise.resolve(this.theme)
    },

    async saveTheme() {
      this.saving = true
      try {
        const { data } = await systemApi.setTheme(this.theme)
        if (isValidTheme(data?.theme)) {
          this.theme = applyTheme(data.theme)
          localStorage.setItem(STORAGE_KEY, this.theme)
        }
        return this.theme
      } finally {
        this.saving = false
      }
    },
  },
})
