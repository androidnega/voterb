<template>
  <div class="tab-nav">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      class="tab-btn"
      :class="[
        tab.tone ? `tab-btn--${tab.tone}` : '',
        { active: modelValue === tab.key },
      ]"
      @click="$emit('update:modelValue', tab.key)"
    >
      <span class="tab-icon" :class="tab.tone ? `tab-icon--${tab.tone}` : ''">
        <i :class="tab.icon"></i>
      </span>
      <span class="tab-label">{{ tab.label }}</span>
      <span
        v-if="tab.count != null"
        class="tab-count"
        :class="tab.tone ? `tab-count--${tab.tone}` : ''"
      >
        {{ tab.count }}
      </span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.tab-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  padding: 0.4rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.875rem;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.85rem 0.5rem 0.5rem;
  border-radius: 0.65rem;
  border: 1px solid transparent;
  background: #fff;
  color: #64748b;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.tab-btn:hover {
  border-color: #e2e8f0;
  color: #334155;
}

.tab-icon {
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  background: #f1f5f9;
  color: #64748b;
  transition: all 0.18s ease;
}

.tab-label {
  line-height: 1;
}

.tab-count {
  min-width: 1.35rem;
  padding: 0.15rem 0.45rem;
  border-radius: 9999px;
  background: #f1f5f9;
  color: #475569;
  font-size: 0.68rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

/* Indigo — Positions */
.tab-icon--indigo { background: #eef2ff; color: #4338ca; }
.tab-btn--indigo:hover { border-color: #c7d2fe; }
.tab-btn--indigo.active {
  background: #eef2ff;
  border-color: #a5b4fc;
  color: #3730a3;
  box-shadow: 0 4px 12px rgba(67, 56, 202, 0.12);
}
.tab-btn--indigo.active .tab-icon--indigo { background: #4338ca; color: #fff; }
.tab-count--indigo { background: #e0e7ff; color: #4338ca; }
.tab-btn--indigo.active .tab-count--indigo { background: #4338ca; color: #fff; }

/* Amber — Candidates */
.tab-icon--amber { background: #fffbeb; color: #b45309; }
.tab-btn--amber:hover { border-color: #fde68a; }
.tab-btn--amber.active {
  background: #fffbeb;
  border-color: #fcd34d;
  color: #92400e;
  box-shadow: 0 4px 12px rgba(180, 83, 9, 0.12);
}
.tab-btn--amber.active .tab-icon--amber { background: #d97706; color: #fff; }
.tab-count--amber { background: #fef3c7; color: #b45309; }
.tab-btn--amber.active .tab-count--amber { background: #d97706; color: #fff; }

/* Teal — Voters */
.tab-icon--teal { background: #ecfdf5; color: #0f766e; }
.tab-btn--teal:hover { border-color: #99f6e4; }
.tab-btn--teal.active {
  background: #ecfdf5;
  border-color: #5eead4;
  color: #0f766e;
  box-shadow: 0 4px 12px rgba(15, 118, 110, 0.12);
}
.tab-btn--teal.active .tab-icon--teal { background: #0f766e; color: #fff; }
.tab-count--teal { background: #d1fae5; color: #047857; }
.tab-btn--teal.active .tab-count--teal { background: #0f766e; color: #fff; }

/* Blue — generic fallback */
.tab-icon--blue { background: #eff6ff; color: #1d4ed8; }
.tab-btn--blue.active {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1d4ed8;
}
.tab-btn--blue.active .tab-icon--blue { background: #1d4ed8; color: #fff; }
.tab-count--blue { background: #dbeafe; color: #1d4ed8; }
.tab-btn--blue.active .tab-count--blue { background: #1d4ed8; color: #fff; }

/* Default active (no tone) */
.tab-btn.active:not([class*='tab-btn--']) {
  background: #ecfdf5;
  border-color: #99f6e4;
  color: #0f766e;
}

.tab-btn.active:not([class*='tab-btn--']) .tab-count {
  background: #0f766e;
  color: #fff;
}
</style>
