import { Chart, registerables } from 'chart.js'
import { MONITOR_THEMES } from '@/composables/useMonitorTheme'

let registered = false

export function ensureChartJs() {
  if (!registered) {
    Chart.register(...registerables)
    registered = true
  }
}

/** Monitor palettes + app shell palette (classic / pulse / amber via CSS vars). */
export const CHART_PALETTES = {
  normal: [...MONITOR_THEMES.normal.colors],
  dark: [...MONITOR_THEMES.dark.colors],
  monokai: [...MONITOR_THEMES.monokai.colors],
}

export function getAccentColor() {
  if (typeof document === 'undefined') return '#3d4f44'
  return getComputedStyle(document.documentElement).getPropertyValue('--vb-accent').trim() || '#3d4f44'
}

export function getAccentSoftColor() {
  if (typeof document === 'undefined') return '#e8efe6'
  return getComputedStyle(document.documentElement).getPropertyValue('--vb-accent-soft').trim() || '#e8efe6'
}

function cssVar(root, name, fallback = '') {
  if (!root) return fallback
  return getComputedStyle(root).getPropertyValue(name).trim() || fallback
}

function appPalette(accent) {
  const sage = cssVar(document.documentElement, '--vb-sage', '#a3b18a')
  const accentBorder = cssVar(document.documentElement, '--vb-accent-border', '#c5d4bc')
  const positive = cssVar(document.documentElement, '--vb-positive', accent)
  const negative = cssVar(document.documentElement, '--vb-negative', '#c45c5c')
  return [accent, sage, accentBorder, '#8a7355', positive, negative]
}

export function resolveAppChartTheme() {
  const root = typeof document !== 'undefined' ? document.documentElement : null
  const accent = cssVar(root, '--vb-accent', '#3d4f44')
  return {
    id: 'app',
    mode: 'light',
    text: cssVar(root, '--vb-muted', '#8a8a8a'),
    grid: cssVar(root, '--vb-line', '#ebeae4'),
    border: cssVar(root, '--vb-surface', '#ffffff'),
    tooltipBg: cssVar(root, '--vb-ink', '#1c1c1c'),
    accent,
    accentSoft: cssVar(root, '--vb-accent-soft', '#e8efe6'),
    colors: appPalette(accent),
  }
}

function paletteFromContainer(root, theme) {
  if (!root) return null
  const style = getComputedStyle(root)
  const raw = style.getPropertyValue('--mr-palette').trim()
  if (raw) {
    const parsed = raw.split(',').map((c) => c.trim()).filter(Boolean)
    if (parsed.length) return parsed
  }
  const collected = []
  for (let i = 1; i <= 8; i += 1) {
    const value = style.getPropertyValue(`--mr-color-${i}`).trim()
    if (value) collected.push(value)
  }
  if (collected.length) return collected
  return CHART_PALETTES[theme] || null
}

export function resolveChartTheme(theme = 'app', containerEl = null) {
  const themeKey = String(theme || 'app')
  if (themeKey === 'app' || themeKey.startsWith('app-')) {
    return resolveAppChartTheme()
  }

  const root = containerEl || (typeof document !== 'undefined' ? document.documentElement : null)
  const palette = paletteFromContainer(root, themeKey) || CHART_PALETTES[themeKey] || CHART_PALETTES.normal

  if (root) {
    const style = getComputedStyle(root)
    const chartGrid = style.getPropertyValue('--mr-chart-grid').trim()
    if (chartGrid) {
      const mode = style.getPropertyValue('--mr-mode').trim() || (themeKey === 'normal' ? 'light' : 'dark')
      return {
        id: themeKey,
        mode,
        text: style.getPropertyValue('--mr-muted').trim() || (mode === 'light' ? '#78716c' : '#94a3b8'),
        grid: chartGrid,
        border: style.getPropertyValue('--mr-chart-border').trim() || (mode === 'light' ? '#ffffff' : '#1e293b'),
        tooltipBg: style.getPropertyValue('--mr-tooltip-bg').trim()
          || (mode === 'light' ? '#ffffff' : 'rgba(15, 23, 42, 0.96)'),
        accent: style.getPropertyValue('--mr-accent').trim() || palette[0],
        accentSoft: style.getPropertyValue('--mr-accent-bg').trim() || `${palette[0]}22`,
        colors: palette,
      }
    }
  }

  const preset = MONITOR_THEMES[themeKey]
  if (preset) {
    return {
      id: themeKey,
      mode: preset.vars['--mr-mode'],
      text: preset.vars['--mr-muted'],
      grid: preset.vars['--mr-chart-grid'],
      border: preset.vars['--mr-chart-border'],
      tooltipBg: preset.vars['--mr-tooltip-bg'],
      accent: preset.vars['--mr-accent'],
      accentSoft: preset.vars['--mr-accent-bg'],
      colors: preset.colors,
    }
  }

  return resolveAppChartTheme()
}

export function baseTooltip(theme) {
  const lightTip = theme.mode === 'light' || theme.id === 'app' || theme.id === 'normal'
  return {
    backgroundColor: theme.tooltipBg,
    titleColor: lightTip ? '#1c1917' : '#f8fafc',
    bodyColor: lightTip ? '#44403c' : '#e2e8f0',
    borderColor: lightTip ? '#e7e5e4' : 'transparent',
    borderWidth: lightTip ? 1 : 0,
    padding: 10,
    cornerRadius: 8,
    titleFont: { size: 12 },
    bodyFont: { size: 13, weight: '600' },
  }
}

export function baseScales(theme, { yBeginAtZero = true } = {}) {
  return {
    y: {
      beginAtZero: yBeginAtZero,
      grid: { color: theme.grid },
      ticks: { color: theme.text, precision: 0, font: { size: 11 } },
      border: { display: false },
    },
    x: {
      grid: { display: false },
      ticks: { color: theme.text, font: { size: 11 } },
      border: { display: false },
    },
  }
}

export function colorAt(theme, index) {
  return theme.colors[index % theme.colors.length]
}

export function buildDonutConfig({ labels, data, theme, legendPosition = 'bottom' }) {
  return {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: labels.map((_, i) => colorAt(theme, i)),
        borderWidth: 2,
        borderColor: theme.border,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: {
          display: labels.length > 0,
          position: legendPosition,
          labels: { color: theme.text, font: { size: 11 }, boxWidth: 10, padding: 12 },
        },
        tooltip: baseTooltip(theme),
      },
    },
  }
}

export function buildBarConfig({ labels, data, theme, horizontal = false, label = 'Votes' }) {
  return {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: labels.map((_, i) => colorAt(theme, i)),
        borderRadius: 6,
        maxBarThickness: horizontal ? 28 : 42,
      }],
    },
    options: {
      indexAxis: horizontal ? 'y' : 'x',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: baseTooltip(theme),
      },
      scales: horizontal
        ? {
            x: { beginAtZero: true, grid: { color: theme.grid }, ticks: { color: theme.text, precision: 0 }, border: { display: false } },
            y: { grid: { display: false }, ticks: { color: theme.text }, border: { display: false } },
          }
        : baseScales(theme),
    },
  }
}

export function buildLineConfig({
  labels,
  datasets,
  theme,
  fill = false,
  tension = 0.4,
  legendPosition = 'top',
  showLegend = false,
}) {
  return {
    type: 'line',
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        borderColor: ds.color || colorAt(theme, i),
        backgroundColor: ds.backgroundColor || (fill ? `${ds.color || colorAt(theme, i)}33` : 'transparent'),
        fill: ds.fill ?? fill,
        tension: ds.tension ?? tension,
        borderWidth: ds.borderWidth ?? 2.5,
        pointRadius: ds.pointRadius ?? 3,
        pointHoverRadius: ds.pointHoverRadius ?? 5,
        pointBackgroundColor: ds.pointBackgroundColor ?? '#ffffff',
        pointBorderColor: ds.pointBorderColor ?? (ds.color || colorAt(theme, i)),
        pointBorderWidth: 2,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: showLegend || datasets.length > 1,
          position: legendPosition,
          labels: { color: theme.text, font: { size: 11 }, boxWidth: 10, padding: 14 },
        },
        tooltip: baseTooltip(theme),
      },
      scales: baseScales(theme),
    },
  }
}

export function buildAreaConfig({ labels, data, label = 'Turnout', theme, color }) {
  const stroke = color || theme.accent || getAccentColor()
  const isDark = theme.mode === 'dark' || theme.id === 'monokai' || theme.id === 'dark'
  const soft = color
    ? `${stroke}33`
    : (isDark ? `${stroke}33` : (theme.accentSoft || getAccentSoftColor()))
  return buildLineConfig({
    labels,
    datasets: [{
      label,
      data,
      color: stroke,
      backgroundColor: soft,
      fill: true,
      tension: 0.45,
      pointRadius: 0,
      pointHoverRadius: 4,
      borderWidth: 2.5,
      pointBackgroundColor: stroke,
      pointBorderColor: stroke,
    }],
    theme,
    showLegend: false,
  })
}

export function createChart(canvas, config) {
  ensureChartJs()
  return new Chart(canvas.getContext('2d'), config)
}

export function destroyChart(instance) {
  if (instance) {
    instance.destroy()
  }
  return null
}
