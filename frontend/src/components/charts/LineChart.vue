<template>
  <BaseChart
    :config="chartConfig"
    :height="height"
    :empty="empty"
    :aria-label="ariaLabel"
    :empty-text="emptyText"
  />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { buildLineConfig, resolveChartTheme } from '@/composables/useChart'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  datasets: { type: Array, default: () => [] },
  fill: { type: Boolean, default: false },
  tension: { type: Number, default: 0.4 },
  theme: { type: String, default: 'app' },
  themeContainer: { type: Object, default: null },
  height: { type: String, default: '14rem' },
  legendPosition: { type: String, default: 'top' },
  showLegend: { type: Boolean, default: false },
  ariaLabel: { type: String, default: 'Line chart' },
  emptyText: { type: String, default: 'No data yet' },
})

const empty = computed(() => {
  if (!props.labels.length || !props.datasets.length) return true
  return !props.datasets.some((ds) => (ds.data || []).some((v) => v > 0))
})

const chartConfig = computed(() => {
  const theme = resolveChartTheme(props.theme, props.themeContainer)
  return buildLineConfig({
    labels: props.labels,
    datasets: props.datasets,
    theme,
    fill: props.fill,
    tension: props.tension,
    legendPosition: props.legendPosition,
    showLegend: props.showLegend,
  })
})
</script>
