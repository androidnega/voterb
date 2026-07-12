<template>
  <div class="gauge-wrap">
    <BaseChart
      :config="chartConfig"
      :height="height"
      :empty="empty"
      :aria-label="ariaLabel"
      :empty-text="emptyText"
    />
    <div class="gauge-wrap__label" aria-hidden="true">{{ displayLabel }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { resolveChartTheme } from '@/composables/useChart'

const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  color: { type: String, default: '#a3b18a' },
  trackColor: { type: String, default: '#e8efe6' },
  theme: { type: String, default: 'normal' },
  themeContainer: { type: Object, default: null },
  height: { type: String, default: '11rem' },
  ariaLabel: { type: String, default: 'Progress gauge' },
  emptyText: { type: String, default: 'No data yet' },
  centerLabel: { type: String, default: '' },
})

const empty = computed(() => props.max <= 0 && props.value <= 0)

const pct = computed(() => {
  if (props.max <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((props.value / props.max) * 100)))
})

const displayLabel = computed(() => props.centerLabel || `${pct.value}%`)

const chartConfig = computed(() => {
  resolveChartTheme(props.theme, props.themeContainer)
  const remaining = Math.max(0, 100 - pct.value)

  return {
    type: 'doughnut',
    data: {
      labels: ['Progress', 'Remaining'],
      datasets: [{
        data: [pct.value, remaining],
        backgroundColor: [props.color, props.trackColor],
        borderWidth: 0,
        circumference: 180,
        rotation: 270,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '78%',
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
      },
    },
  }
})
</script>

<style scoped>
.gauge-wrap {
  position: relative;
}

.gauge-wrap__label {
  position: absolute;
  left: 50%;
  bottom: 8%;
  transform: translateX(-50%);
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--vb-ink, #1c1c1c);
  pointer-events: none;
}
</style>
