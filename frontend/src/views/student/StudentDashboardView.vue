<template>
  <div>
    <!-- Tab Navigation -->
    <div class="flex border-b border-gray-200 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        class="py-3 px-4 text-sm font-medium transition-colors duration-200 border-b-2"
        :class="activeTab === tab.key 
          ? 'border-emerald-600 text-emerald-700' 
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
      >
        <i :class="tab.icon" class="mr-2"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div v-if="activeTab === 'elections'">
      <StudentElectionsView />
    </div>
    <div v-else-if="activeTab === 'results'">
      <StudentResultsView />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import StudentElectionsView from '@/components/student/StudentElectionsView.vue'
import StudentResultsView from '@/views/student/StudentResultsView.vue'

const tabs = [
  { key: 'elections', label: 'Elections', icon: 'pi pi-check-square' },
  { key: 'results', label: 'Results', icon: 'pi pi-chart-bar' }
]

const activeTab = ref('elections')
</script>
