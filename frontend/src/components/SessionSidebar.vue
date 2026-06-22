<script setup lang="ts">
import { ref } from 'vue'
import type { Session } from '../types'

defineProps<{
  sessions: Session[]
  activeSessionId: string
}>()

const emit = defineEmits<{
  select: [sessionId: string]
  new: []
  delete: [sessionId: string]
}>()

const hoverId = ref<string | null>(null)

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="w-64 bg-gray-900 text-white flex flex-col h-full">
    <!-- 头部 -->
    <div class="p-3 border-b border-gray-700">
      <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">
        💬 对话列表
      </h2>
      <button
        class="w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
        @click="emit('new')"
      >
        + 新对话
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="sessions.length === 0" class="p-4 text-center text-gray-500 text-sm">
        暂无对话记录
      </div>
      <div
        v-for="session in sessions"
        :key="session.id"
        :class="[
          'group flex items-center justify-between px-3 py-2.5 cursor-pointer transition-colors',
          session.id === activeSessionId
            ? 'bg-gray-700 border-l-2 border-blue-500'
            : 'hover:bg-gray-800 border-l-2 border-transparent'
        ]"
        @mouseenter="hoverId = session.id"
        @mouseleave="hoverId = null"
        @click="emit('select', session.id)"
      >
        <div class="flex-1 min-w-0">
          <div
            :class="[
              'text-sm truncate',
              session.id === activeSessionId ? 'text-white' : 'text-gray-300'
            ]"
          >
            {{ session.title }}
          </div>
          <div class="text-xs text-gray-500 mt-0.5">
            {{ formatDate(session.updated_at) }}
          </div>
        </div>
        <button
          v-if="hoverId === session.id"
          class="ml-2 p-1 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded transition-colors flex-shrink-0"
          title="删除对话"
          @click.stop="emit('delete', session.id)"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="p-3 border-t border-gray-700 text-xs text-gray-500">
      共 {{ sessions.length }} 个对话
    </div>
  </div>
</template>