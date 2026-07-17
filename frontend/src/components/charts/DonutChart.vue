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
import { buildDonutConfig, resolveChartTheme } from '@/composables/useChart'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  data: { type: Array, default: () => [] },
  theme: { type: String, default: 'app' },
  themeContainer: { type: Object, default: null },
  height: { type: String, default: '14rem' },
  legendPosition: { type: String, default: 'bottom' },
  ariaLabel: { type: String, default: 'Donut chart' },
  emptyText: { type: String, default: 'No data yet' },
})

const empty = computed(() => !props.labels.length || !props.data.some((v) => v > 0))

const chartConfig = computed(() => {
  const theme = resolveChartTheme(props.theme, props.themeContainer)
  return buildDonutConfig({
    labels: props.labels,
    data: props.data,
    theme,
    legendPosition: props.legendPosition,
  })
})
</script>
