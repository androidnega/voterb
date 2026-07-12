import { defineStore } from 'pinia'
import { systemApi } from '@/api/system'

const THEME_KEY = 'voterb_ui_theme'
const DASHBOARD_KEY = 'voterb_ui_dashboard'

export const THEME_IDS = ['classic', 'pulse', 'amber']
export const DASHBOARD_IDS = ['atelier', 'operations', 'lumen']

const FALLBACK_THEME_OPTIONS = [
  { id: 'classic', label: 'Classic', description: 'Sage soft-UI palette for the admin shell' },
  { id: 'pulse', label: 'Pulse', description: 'Coral accent on light surfaces' },
  { id: 'amber', label: 'Amber', description: 'Warm cream surfaces with gold and charcoal accents' },
]

const FALLBACK_DASHBOARD_OPTIONS = [
  {
    id: 'atelier',
    label: 'Atelier Soft',
    description: 'Card mosaic with turnout gauge, sparklines, and activity — the current admin dashboard.',
  },
  {
    id: 'operations',
    label: 'Operations',
    description: 'Compact stats, charts, and quick-access links for dense election ops.',
  },
  {
    id: 'lumen',
    label: 'Lumen',
    description: 'Warm soft-UI workspace with gauge, schedule cards, KPI chart, and activity table.',
  },
]

function isValidTheme(theme) {
  return THEME_IDS.includes(theme)
}

function isValidDashboard(dashboard) {
  return DASHBOARD_IDS.includes(dashboard)
}

function applyTheme(theme) {
  const resolved = isValidTheme(theme) ? theme : 'classic'
  document.documentElement.dataset.theme = resolved
  return resolved
}

function applyDashboard(dashboard) {
  const resolved = isValidDashboard(dashboard) ? dashboard : 'atelier'
  document.documentElement.dataset.dashboard = resolved
  return resolved
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: applyTheme(localStorage.getItem(THEME_KEY) || 'classic'),
    dashboard: applyDashboard(localStorage.getItem(DASHBOARD_KEY) || 'atelier'),
    options: [...FALLBACK_THEME_OPTIONS],
    dashboardOptions: [...FALLBACK_DASHBOARD_OPTIONS],
    loaded: false,
    saving: false,
  }),

  getters: {
    isPulse: (state) => state.theme === 'pulse',
    isAmber: (state) => state.theme === 'amber',
    isAtelierDashboard: (state) => state.dashboard === 'atelier',
    isOperationsDashboard: (state) => state.dashboard === 'operations',
    isLumenDashboard: (state) => state.dashboard === 'lumen',
  },

  actions: {
    async bootstrap() {
      try {
        const { data } = await systemApi.getTheme()
        if (data?.options?.length) this.options = data.options
        if (data?.dashboard_options?.length) this.dashboardOptions = data.dashboard_options
        if (isValidTheme(data?.theme)) {
          this.theme = applyTheme(data.theme)
          localStorage.setItem(THEME_KEY, this.theme)
        }
        if (isValidDashboard(data?.dashboard)) {
          this.dashboard = applyDashboard(data.dashboard)
          localStorage.setItem(DASHBOARD_KEY, this.dashboard)
        }
      } catch {
        // Keep cached/local prefs when API is unavailable
      } finally {
        this.loaded = true
      }
    },

    setTheme(theme, { persistRemote = false } = {}) {
      if (!isValidTheme(theme)) return Promise.resolve(this.theme)
      this.theme = applyTheme(theme)
      localStorage.setItem(THEME_KEY, this.theme)
      if (persistRemote) return this.saveAppearance()
      return Promise.resolve(this.theme)
    },

    setDashboard(dashboard, { persistRemote = false } = {}) {
      if (!isValidDashboard(dashboard)) return Promise.resolve(this.dashboard)
      this.dashboard = applyDashboard(dashboard)
      localStorage.setItem(DASHBOARD_KEY, this.dashboard)
      if (persistRemote) return this.saveAppearance()
      return Promise.resolve(this.dashboard)
    },

    async saveAppearance() {
      this.saving = true
      try {
        const { data } = await systemApi.setTheme({
          theme: this.theme,
          dashboard: this.dashboard,
        })
        if (isValidTheme(data?.theme)) {
          this.theme = applyTheme(data.theme)
          localStorage.setItem(THEME_KEY, this.theme)
        }
        if (isValidDashboard(data?.dashboard)) {
          this.dashboard = applyDashboard(data.dashboard)
          localStorage.setItem(DASHBOARD_KEY, this.dashboard)
        }
        return { theme: this.theme, dashboard: this.dashboard }
      } finally {
        this.saving = false
      }
    },

    /** @deprecated use saveAppearance */
    async saveTheme() {
      return this.saveAppearance()
    },
  },
})
