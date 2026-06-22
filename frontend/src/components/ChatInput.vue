<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

const input = ref('')

function handleSubmit(e: Event) {
  e.preventDefault()
  if (input.value.trim()) {
    emit('send', input.value.trim())
    input.value = ''
  }
}
</script>

<template>
  <form @submit="handleSubmit" class="p-4 bg-white border-t">
    <div class="flex gap-2">
      <input
        v-model="input"
        type="text"
        :disabled="disabled"
        :placeholder="disabled ? '等待回复...' : '输入您的问题...'"
        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      />
      <button
        type="submit"
        :disabled="disabled || !input.trim()"
        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        发送
      </button>
    </div>
  </form>
</template>