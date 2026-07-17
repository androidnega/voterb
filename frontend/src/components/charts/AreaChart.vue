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
import { buildAreaConfig, resolveChartTheme } from '@/composables/useChart'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  data: { type: Array, default: () => [] },
  label: { type: String, default: 'Turnout' },
  color: { type: String, default: '' },
  theme: { type: String, default: 'app' },
  themeContainer: { type: Object, default: null },
  height: { type: String, default: '14rem' },
  ariaLabel: { type: String, default: 'Area chart' },
  emptyText: { type: String, default: 'No data yet' },
})

const empty = computed(() => !props.labels.length)

const chartConfig = computed(() => {
  const theme = resolveChartTheme(props.theme, props.themeContainer)
  return buildAreaConfig({
    labels: props.labels,
    data: props.data,
    label: props.label,
    theme,
    color: props.color || undefined,
  })
})
</script>
