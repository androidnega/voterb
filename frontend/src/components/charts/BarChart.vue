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
import { buildBarConfig, resolveChartTheme } from '@/composables/useChart'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  data: { type: Array, default: () => [] },
  label: { type: String, default: 'Votes' },
  theme: { type: String, default: 'app' },
  themeContainer: { type: Object, default: null },
  height: { type: String, default: '14rem' },
  ariaLabel: { type: String, default: 'Bar chart' },
  emptyText: { type: String, default: 'No data yet' },
})

const empty = computed(() => !props.labels.length || !props.data.some((v) => v > 0))

const chartConfig = computed(() => {
  const theme = resolveChartTheme(props.theme, props.themeContainer)
  return buildBarConfig({
    labels: props.labels,
    data: props.data,
    theme,
    label: props.label,
  })
})
</script>
