import { ref, computed } from 'vue'

const STORAGE_KEY = 'voterb_monitor_theme'
export const MONITOR_THEME_ORDER = ['normal', 'dark', 'monokai']

export const MONITOR_THEMES = {
  /** Light / white “Normal” mode */
  normal: {
    id: 'normal',
    label: 'Normal',
    colors: ['#0f766e', '#2563eb', '#d97706', '#7c3aed', '#dc2626', '#db2777'],
    vars: {
      '--mr-mode': 'light',
      '--mr-bg': '#f7f6f3',
      '--mr-panel': '#ffffff',
      '--mr-panel-border': '#e8e6e1',
      '--mr-topbar': '#ffffff',
      '--mr-topbar-border': '#e8e6e1',
      '--mr-accent': '#0f766e',
      '--mr-accent-soft': '#0d9488',
      '--mr-accent-bg': 'rgba(15, 118, 110, 0.08)',
      '--mr-accent-border': 'rgba(15, 118, 110, 0.22)',
      '--mr-on-accent': '#ffffff',
      '--mr-text': '#1c1917',
      '--mr-muted': '#78716c',
      '--mr-subtle': '#a8a29e',
      '--mr-track': '#e7e5e4',
      '--mr-row': '#fafaf9',
      '--mr-chart-grid': '#e7e5e4',
      '--mr-chart-border': '#ffffff',
      '--mr-tooltip-bg': '#ffffff',
      '--mr-scrollbar-track': '#f5f5f4',
      '--mr-scrollbar-thumb': '#d6d3d1',
    },
  },
  /** Dark slate ops mode */
  dark: {
    id: 'dark',
    label: 'Dark',
    colors: ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899'],
    vars: {
      '--mr-mode': 'dark',
      '--mr-bg': '#0f172a',
      '--mr-panel': 'rgba(30, 41, 59, 0.92)',
      '--mr-panel-border': 'rgba(51, 65, 85, 0.7)',
      '--mr-topbar': '#0f172a',
      '--mr-topbar-border': 'rgba(51, 65, 85, 0.85)',
      '--mr-accent': '#10b981',
      '--mr-accent-soft': '#6ee7b7',
      '--mr-accent-bg': 'rgba(16, 185, 129, 0.14)',
      '--mr-accent-border': 'rgba(16, 185, 129, 0.35)',
      '--mr-on-accent': '#0f172a',
      '--mr-text': '#f8fafc',
      '--mr-muted': '#94a3b8',
      '--mr-subtle': '#64748b',
      '--mr-track': 'rgba(51, 65, 85, 0.85)',
      '--mr-row': 'rgba(51, 65, 85, 0.38)',
      '--mr-chart-grid': '#334155',
      '--mr-chart-border': '#1e293b',
      '--mr-tooltip-bg': 'rgba(15, 23, 42, 0.96)',
      '--mr-scrollbar-track': '#1e293b',
      '--mr-scrollbar-thumb': '#334155',
    },
  },
  monokai: {
    id: 'monokai',
    label: 'Monokai',
    colors: ['#a6e22e', '#66d9ef', '#fd971f', '#f92672', '#ae81ff', '#e6db74'],
    vars: {
      '--mr-mode': 'dark',
      '--mr-bg': '#272822',
      '--mr-panel': 'rgba(39, 40, 34, 0.96)',
      '--mr-panel-border': 'rgba(73, 72, 62, 0.9)',
      '--mr-topbar': '#1e1f1c',
      '--mr-topbar-border': 'rgba(73, 72, 62, 0.95)',
      '--mr-accent': '#a6e22e',
      '--mr-accent-soft': '#a6e22e',
      '--mr-accent-bg': 'rgba(166, 226, 46, 0.12)',
      '--mr-accent-border': 'rgba(166, 226, 46, 0.4)',
      '--mr-on-accent': '#272822',
      '--mr-text': '#f8f8f2',
      '--mr-muted': '#75715e',
      '--mr-subtle': '#49483e',
      '--mr-track': 'rgba(73, 72, 62, 0.9)',
      '--mr-row': 'rgba(49, 50, 44, 0.85)',
      '--mr-chart-grid': '#49483e',
      '--mr-chart-border': '#272822',
      '--mr-tooltip-bg': '#272822',
      '--mr-scrollbar-track': '#272822',
      '--mr-scrollbar-thumb': '#49483e',
    },
  },
}

function migrateThemeId(raw) {
  if (MONITOR_THEMES[raw]) return raw
  // Legacy: previous dual toggle stored "normal" as the dark slate look
  if (raw === 'slate' || raw === 'night') return 'dark'
  return 'normal'
}

function buildThemeStyle(theme) {
  const style = { ...theme.vars }
  theme.colors.forEach((hex, i) => {
    style[`--mr-color-${i + 1}`] = hex
  })
  style['--mr-palette'] = theme.colors.join(',')
  return style
}

export function useMonitorTheme() {
  const themeId = ref(migrateThemeId(localStorage.getItem(STORAGE_KEY) || 'normal'))

  const theme = computed(() => MONITOR_THEMES[themeId.value] || MONITOR_THEMES.normal)
  const chartColors = computed(() => theme.value.colors)
  const isMonokai = computed(() => themeId.value === 'monokai')
  const isLight = computed(() => theme.value.vars['--mr-mode'] === 'light')
  const themeStyle = computed(() => buildThemeStyle(theme.value))
  const nextThemeLabel = computed(() => {
    const i = MONITOR_THEME_ORDER.indexOf(themeId.value)
    const next = MONITOR_THEME_ORDER[(i + 1) % MONITOR_THEME_ORDER.length]
    return MONITOR_THEMES[next].label
  })

  const toggleTheme = () => {
    const i = MONITOR_THEME_ORDER.indexOf(themeId.value)
    themeId.value = MONITOR_THEME_ORDER[(i + 1) % MONITOR_THEME_ORDER.length]
    localStorage.setItem(STORAGE_KEY, themeId.value)
  }

  const colorAt = (index) => {
    const colors = chartColors.value
    return colors[index % colors.length]
  }

  return {
    themeId,
    theme,
    chartColors,
    isMonokai,
    isLight,
    themeStyle,
    nextThemeLabel,
    toggleTheme,
    colorAt,
  }
}
