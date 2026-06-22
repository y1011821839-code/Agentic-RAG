<script setup lang="ts">
defineProps<{
  uploading: boolean
  documentCount: number
}>()

const emit = defineEmits<{
  upload: [file: File]
  clear: []
}>()

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    emit('upload', file)
    target.value = ''
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-md p-4">
    <h3 class="text-lg font-semibold mb-3 text-gray-800">📚 知识库管理</h3>

    <div class="mb-4">
      <label class="block w-full cursor-pointer">
        <div
          :class="[
            'border-2 border-dashed border-gray-300 rounded-lg p-6 text-center transition-colors',
            uploading ? 'bg-gray-100' : 'hover:border-blue-500 hover:bg-blue-50'
          ]"
        >
          <input
            type="file"
            accept=".txt,.md"
            :disabled="uploading"
            class="hidden"
            @change="handleFileChange"
          />
          <template v-if="uploading">
            <div class="text-gray-600">⏳ 上传中...</div>
          </template>
          <template v-else>
            <div class="text-blue-600 mb-2">📤 点击上传文档</div>
            <div class="text-gray-500 text-sm">支持 .txt 和 .md 格式</div>
          </template>
        </div>
      </label>
    </div>

    <div class="flex justify-between items-center text-sm text-gray-600">
      <span>当前文档数量：{{ documentCount }} 个块</span>
      <button
        v-if="documentCount > 0"
        class="text-red-600 hover:text-red-700 hover:underline"
        @click="emit('clear')"
      >
        清空知识库
      </button>
    </div>
  </div>
</template>