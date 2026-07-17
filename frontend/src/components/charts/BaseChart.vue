<template>
  <div
    class="chart-host"
    :style="{ height }"
    role="img"
    :aria-label="ariaLabel"
  >
    <canvas ref="canvasRef"></canvas>
    <div v-if="showEmpty" class="chart-host__empty">
      <slot name="empty">
        <i class="fas fa-chart-pie"></i>
        <p>{{ emptyText }}</p>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { createChart, destroyChart } from '@/composables/useChart'

const props = defineProps({
  config: { type: Object, default: null },
  height: { type: String, default: '14rem' },
  ariaLabel: { type: String, default: 'Chart' },
  emptyText: { type: String, default: 'No data yet' },
  empty: { type: Boolean, default: false },
})

const canvasRef = ref(null)
let chartInstance = null

const showEmpty = computed(() => props.empty || !props.config)

const render = async () => {
  await nextTick()
  if (chartInstance) {
    chartInstance = destroyChart(chartInstance)
  }
  if (!canvasRef.value || !props.config || props.empty) return
  chartInstance = createChart(canvasRef.value, props.config)
}

watch(() => props.config, render, { deep: true })
watch(() => props.empty, render)

onMounted(render)
onUnmounted(() => {
  chartInstance = destroyChart(chartInstance)
})

defineExpose({ render })
</script>

<style scoped>
.chart-host {
  position: relative;
  width: 100%;
}

.chart-host canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-host__empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--mr-muted, var(--vb-muted, #8a8a8a));
  font-size: 0.875rem;
  background: color-mix(in srgb, var(--mr-panel, var(--vb-surface, #ffffff)) 88%, transparent);
  border-radius: 0.65rem;
}

.chart-host__empty i {
  font-size: 1.75rem;
  color: #cbd5e1;
}
</style>
