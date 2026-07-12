import { ref, computed } from 'vue'

const STORAGE_KEY = 'voterb_monitor_theme'

export const MONITOR_THEMES = {
  normal: {
    id: 'normal',
    label: 'Normal',
    colors: ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899'],
    vars: {
      '--mr-bg': 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      '--mr-panel': 'rgba(30, 41, 59, 0.72)',
      '--mr-panel-border': 'rgba(51, 65, 85, 0.55)',
      '--mr-topbar': 'rgba(15, 23, 42, 0.92)',
      '--mr-topbar-border': 'rgba(51, 65, 85, 0.6)',
      '--mr-accent': '#10b981',
      '--mr-accent-soft': '#6ee7b7',
      '--mr-accent-bg': 'rgba(16, 185, 129, 0.14)',
      '--mr-accent-border': 'rgba(16, 185, 129, 0.35)',
      '--mr-text': '#f8fafc',
      '--mr-muted': '#94a3b8',
      '--mr-subtle': '#64748b',
      '--mr-track': 'rgba(51, 65, 85, 0.85)',
      '--mr-row': 'rgba(51, 65, 85, 0.38)',
      '--mr-chart-grid': '#334155',
      '--mr-chart-border': '#1e293b',
      '--mr-scrollbar-track': '#1e293b',
      '--mr-scrollbar-thumb': '#334155',
    },
  },
  monokai: {
    id: 'monokai',
    label: 'Monokai',
    colors: ['#a6e22e', '#66d9ef', '#fd971f', '#f92672', '#ae81ff', '#e6db74'],
    vars: {
      '--mr-bg': '#272822',
      '--mr-panel': 'rgba(39, 40, 34, 0.92)',
      '--mr-panel-border': 'rgba(73, 72, 62, 0.85)',
      '--mr-topbar': 'rgba(30, 31, 28, 0.96)',
      '--mr-topbar-border': 'rgba(73, 72, 62, 0.9)',
      '--mr-accent': '#a6e22e',
      '--mr-accent-soft': '#a6e22e',
      '--mr-accent-bg': 'rgba(166, 226, 46, 0.12)',
      '--mr-accent-border': 'rgba(166, 226, 46, 0.4)',
      '--mr-text': '#f8f8f2',
      '--mr-muted': '#75715e',
      '--mr-subtle': '#49483e',
      '--mr-track': 'rgba(73, 72, 62, 0.9)',
      '--mr-row': 'rgba(49, 50, 44, 0.85)',
      '--mr-chart-grid': '#49483e',
      '--mr-chart-border': '#272822',
      '--mr-scrollbar-track': '#272822',
      '--mr-scrollbar-thumb': '#49483e',
    },
  },
}

export function useMonitorTheme() {
  const themeId = ref(localStorage.getItem(STORAGE_KEY) || 'normal')

  const theme = computed(() => MONITOR_THEMES[themeId.value] || MONITOR_THEMES.normal)
  const chartColors = computed(() => theme.value.colors)
  const isMonokai = computed(() => themeId.value === 'monokai')

  const themeStyle = computed(() => theme.value.vars)

  const toggleTheme = () => {
    themeId.value = themeId.value === 'monokai' ? 'normal' : 'monokai'
    localStorage.setItem(STORAGE_KEY, themeId.value)
  }

  return { themeId, theme, chartColors, isMonokai, themeStyle, toggleTheme }
}
