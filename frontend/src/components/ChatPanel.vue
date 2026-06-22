<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.min.css'
import type { Message } from '../types'

const props = defineProps<{
  messages: Message[]
  loading?: boolean
  thinkingStatus?: string
}>()

const messagesEndRef = ref<HTMLDivElement>()

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch {
        // fallback
      }
    }
    return ''
  },
})

function renderMarkdown(content: string): string {
  return md.render(content)
}

watch(
  () => props.messages.length,
  () => {
    nextTick(() => {
      messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
    })
  }
)
</script>

<template>
  <div class="flex-1 overflow-y-auto p-4 space-y-4">
    <div
      v-for="message in messages"
      :key="message.id"
      :class="['flex', message.role === 'user' ? 'justify-end' : 'justify-start']"
    >
      <div
        :class="[
          'max-w-[70%] rounded-lg p-4 shadow-md',
          message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white text-gray-800'
        ]"
      >
        <div
          class="prose prose-sm max-w-none"
          v-html="renderMarkdown(message.content)"
        />

        <div
          v-if="message.sources && message.sources.length > 0"
          :class="[
            'mt-3 pt-3 border-t text-sm',
            message.role === 'user' ? 'border-blue-500' : 'border-gray-200'
          ]"
        >
          <div
            :class="[
              'font-semibold mb-2',
              message.role === 'user' ? 'text-blue-200' : 'text-gray-600'
            ]"
          >
            📖 引用来源：
          </div>
          <div
            v-for="(source, idx) in message.sources"
            :key="idx"
            :class="[
              'p-2 rounded mb-1 text-xs',
              message.role === 'user' ? 'bg-blue-700' : 'bg-gray-50'
            ]"
          >
            <div class="truncate">{{ source.content }}</div>
            <div
              v-if="source.metadata?.source"
              :class="[
                'mt-1',
                message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
              ]"
            >
              来源：{{ source.metadata.source }}
            </div>
          </div>
        </div>

        <div
          v-if="message.toolsUsed && message.toolsUsed.length > 0"
          :class="[
            'mt-2 text-xs',
            message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
          ]"
        >
          🔧 使用工具：{{ message.toolsUsed.join(', ') }}
        </div>

        <div
          :class="[
            'text-xs mt-2',
            message.role === 'user' ? 'text-blue-200' : 'text-gray-400'
          ]"
        >
          {{ message.timestamp.toLocaleTimeString() }}
        </div>
      </div>
    </div>

    <!-- 思考中指示器 -->
    <div v-if="thinkingStatus" class="flex justify-start">
      <div class="bg-gray-50 rounded-lg p-3 shadow-md border border-gray-200 animate-pulse">
        <div class="flex items-center gap-2 text-sm text-gray-600">
          <span class="flex gap-1">
            <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms" />
            <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 200ms" />
            <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 400ms" />
          </span>
          <span>思考中：{{ thinkingStatus }}</span>
        </div>
      </div>
    </div>

    <div ref="messagesEndRef" />
  </div>
</template>