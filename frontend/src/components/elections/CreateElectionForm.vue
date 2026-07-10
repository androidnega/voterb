<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <InputText v-model="form.title" class="w-full" required />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
      <Textarea v-model="form.description" rows="3" class="w-full" />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
      <Dropdown 
        v-model="form.election_type" 
        :options="types" 
        optionLabel="label" 
        optionValue="value" 
        placeholder="Select type" 
        class="w-full" 
      />
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
        <Calendar v-model="form.start_date" showTime hourFormat="24" class="w-full" required />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">End Date *</label>
        <Calendar v-model="form.end_date" showTime hourFormat="24" class="w-full" required />
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Voting Channels</label>
      <div class="flex items-center space-x-4">
        <div class="flex items-center">
          <Checkbox v-model="form.allow_web_voting" binary />
          <label class="ml-2 text-sm">Web</label>
        </div>
        <div class="flex items-center">
          <Checkbox v-model="form.allow_ussd_voting" binary />
          <label class="ml-2 text-sm">USSD</label>
        </div>
      </div>
    </div>
    <div class="flex justify-end space-x-3 pt-4">
      <Button label="Cancel" severity="secondary" @click="$emit('cancel')" />
      <Button label="Create" type="submit" :loading="loading" />
    </div>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { electionApi } from '@/api/elections'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'

const emit = defineEmits(['success', 'cancel'])

const types = [
  { label: 'General', value: 'general' },
  { label: 'Student Union', value: 'student_union' },
  { label: 'Faculty', value: 'faculty' },
  { label: 'Departmental', value: 'departmental' },
  { label: 'Special', value: 'special' }
]

const form = ref({
  title: '',
  description: '',
  election_type: 'general',
  start_date: null,
  end_date: null,
  allow_web_voting: true,
  allow_ussd_voting: false
})

const loading = ref(false)

const handleSubmit = async () => {
  if (!form.value.start_date || !form.value.end_date) {
    alert('Please set both start and end dates.')
    return
  }
  if (new Date(form.value.end_date) <= new Date(form.value.start_date)) {
    alert('End date must be after the start date.')
    return
  }

  loading.value = true
  try {
    const payload = {
      ...form.value,
      start_date: new Date(form.value.start_date).toISOString(),
      end_date: new Date(form.value.end_date).toISOString(),
    }
    await electionApi.create(payload)
    emit('success')
  } catch (error) {
    console.error('Failed to create election:', error)
    alert('Failed to create election. Please check the form.')
  } finally {
    loading.value = false
  }
}
</script>
