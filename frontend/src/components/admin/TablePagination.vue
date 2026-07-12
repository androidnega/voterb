<template>
  <div class="table-pagination">
    <p class="pagination-meta">
      <template v-if="total > 0">
        Showing <strong>{{ from }}</strong>–<strong>{{ to }}</strong> of <strong>{{ total }}</strong>
      </template>
      <template v-else>No results</template>
    </p>

    <div class="pagination-controls">
      <label class="page-size">
        <span>Rows</span>
        <select :value="pageSize" @change="onSizeChange">
          <option v-for="option in pageSizeOptions" :key="option" :value="option">{{ option }}</option>
        </select>
      </label>

      <div class="page-buttons">
        <button type="button" class="page-btn" :disabled="page <= 1" @click="$emit('update:page', page - 1)">
          <i class="fas fa-chevron-left"></i>
        </button>
        <span class="page-indicator">{{ page }} / {{ totalPages }}</span>
        <button type="button" class="page-btn" :disabled="page >= totalPages" @click="$emit('update:page', page + 1)">
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  total: { type: Number, required: true },
  from: { type: Number, required: true },
  to: { type: Number, required: true },
  pageSizeOptions: { type: Array, default: () => [10, 20, 50] },
})

const emit = defineEmits(['update:page', 'update:pageSize'])

const onSizeChange = (event) => {
  emit('update:pageSize', Number(event.target.value))
}
</script>

<style scoped>
.table-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1.25rem;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}

.pagination-meta {
  font-size: 0.8125rem;
  color: #64748b;
}

.pagination-meta strong {
  color: #0f172a;
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.page-size {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.page-size select {
  padding: 0.35rem 0.55rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  font-size: 0.8125rem;
  color: #334155;
}

.page-buttons {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.page-btn {
  width: 2rem;
  height: 2rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #fff;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
}

.page-btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #0f766e;
}

.page-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.page-indicator {
  min-width: 3.5rem;
  text-align: center;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #334155;
}
</style>
