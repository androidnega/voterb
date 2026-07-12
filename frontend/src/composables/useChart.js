import { Chart, registerables } from 'chart.js'

let registered = false

export function ensureChartJs() {
  if (!registered) {
    Chart.register(...registerables)
    registered = true
  }
}

export const CHART_PALETTES = {
  normal: ['#a3b18a', '#3d4f44', '#c5d4bc', '#8a7355', '#6b7f71', '#d4c4a8'],
  monokai: ['#a6e22e', '#66d9ef', '#fd971f', '#f92672', '#ae81ff', '#e6db74'],
}

export function getAccentColor() {
  if (typeof document === 'undefined') return '#3d4f44'
  return getComputedStyle(document.documentElement).getPropertyValue('--vb-accent').trim() || '#3d4f44'
}

export function getAccentSoftColor() {
  if (typeof document === 'undefined') return '#e8efe6'
  return getComputedStyle(document.documentElement).getPropertyValue('--vb-accent-soft').trim() || '#e8efe6'
}

export function resolveChartTheme(theme = 'normal', containerEl = null) {
  const root = containerEl || (typeof document !== 'undefined' ? document.documentElement : null)

  if (root) {
    const style = getComputedStyle(root)
    const chartGrid = style.getPropertyValue('--mr-chart-grid').trim()
    if (chartGrid) {
      return {
        id: theme,
        text: style.getPropertyValue('--mr-muted').trim() || '#94a3b8',
        grid: chartGrid,
        border: style.getPropertyValue('--mr-chart-border').trim() || '#1e293b',
        tooltipBg: theme === 'monokai' ? '#272822' : 'rgba(15, 23, 42, 0.92)',
        accent: style.getPropertyValue('--mr-accent').trim() || '#10b981',
        colors: theme === 'monokai' ? CHART_PALETTES.monokai : CHART_PALETTES.normal,
      }
    }
  }

  if (theme === 'monokai' && root) {
    const style = getComputedStyle(root)
    return {
      id: 'monokai',
      text: style.getPropertyValue('--mr-muted').trim() || '#75715e',
      grid: style.getPropertyValue('--mr-chart-grid').trim() || '#49483e',
      border: style.getPropertyValue('--mr-chart-border').trim() || '#272822',
      tooltipBg: '#272822',
      accent: style.getPropertyValue('--mr-accent').trim() || '#a6e22e',
      colors: CHART_PALETTES.monokai,
    }
  }

  return {
    id: 'normal',
    text: '#8a8a8a',
    grid: '#f0efe9',
    border: '#ffffff',
    tooltipBg: '#1c1c1c',
    accent: getAccentColor(),
    colors: CHART_PALETTES.normal,
  }
}

export function baseTooltip(theme) {
  return {
    backgroundColor: theme.tooltipBg,
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
  const soft = theme.id === 'monokai' || theme.grid === '#334155' || theme.grid === '#49483e'
    ? `${stroke}33`
    : (color ? `${stroke}33` : getAccentSoftColor())
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
