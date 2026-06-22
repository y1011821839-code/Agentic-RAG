<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import ChatInput from './components/ChatInput.vue'
import DocumentUpload from './components/DocumentUpload.vue'
import SessionSidebar from './components/SessionSidebar.vue'
import type { Message, Session } from './types'
import {
  sendChatStream,
  uploadDocument,
  getDocumentCount,
  clearDocuments,
  listSessions,
  getSession,
  createSession,
  deleteSession,
} from './utils/api'

const messages = ref<Message[]>([])
const loading = ref(false)
const thinkingStatus = ref('')
const uploading = ref(false)
const documentCount = ref(0)
const sessionId = ref('')
const sessions = ref<Session[]>([])

onMounted(() => {
  fetchDocumentCount()
  initSessions()
})

async function initSessions() {
  try {
    const list = await listSessions()
    sessions.value = list
    if (list.length > 0) {
      switchToSession(list[0].id)
    } else {
      const newId = await createSession()
      sessions.value = await listSessions()
      sessionId.value = newId
    }
  } catch (e) {
    console.error('初始化会话失败:', e)
  }
}

async function refreshSessionList() {
  try {
    sessions.value = await listSessions()
  } catch (e) {
    console.error('刷新会话列表失败:', e)
  }
}

async function switchToSession(id: string) {
  try {
    const data = await getSession(id)
    sessionId.value = id
    if (data.messages) {
      messages.value = data.messages.map((msg: any) => ({
        id: `${msg.timestamp}-${msg.role}`,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
      }))
    } else {
      messages.value = []
    }
  } catch (e) {
    console.error('加载会话失败:', e)
  }
}

async function handleNewChat() {
  try {
    const newId = await createSession()
    sessionId.value = newId
    messages.value = []
    await refreshSessionList()
  } catch (e) {
    console.error('创建新会话失败:', e)
  }
}

async function handleDeleteSession(id: string) {
  try {
    await deleteSession(id)
    await refreshSessionList()
    const updatedList = await listSessions()
    sessions.value = updatedList
    if (id === sessionId.value) {
      if (updatedList.length > 0) {
        switchToSession(updatedList[0].id)
      } else {
        const newId = await createSession()
        sessionId.value = newId
        messages.value = []
        await refreshSessionList()
      }
    }
  } catch (e) {
    console.error('删除会话失败:', e)
  }
}

async function fetchDocumentCount() {
  try {
    documentCount.value = await getDocumentCount()
  } catch (error) {
    console.error('获取文档数量失败:', error)
  }
}

async function handleSend(question: string) {
  const assistantId = (Date.now() + 1).toString()

  messages.value = [...messages.value, {
    id: Date.now().toString(),
    role: 'user',
    content: question,
    timestamp: new Date(),
  }]

  loading.value = true
  thinkingStatus.value = ''

  try {
    const history = messages.value.slice(0, -1).map((msg) => ({
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp.toISOString(),
    }))

    let fullAnswer = ''

    await sendChatStream(question, history, (event) => {
      switch (event.type) {
        case 'thinking':
          thinkingStatus.value = event.content
          break

        case 'session_id':
          if (!sessionId.value) {
            sessionId.value = event.content
          }
          break

        case 'token':
          fullAnswer += event.content
          {
            const idx = messages.value.findIndex((m) => m.id === assistantId)
            const msg: Message = {
              id: assistantId,
              role: 'assistant',
              content: fullAnswer,
              timestamp: new Date(),
              sources: [],
              toolsUsed: [],
            }
            if (idx >= 0) {
              messages.value = [...messages.value.slice(0, idx), msg, ...messages.value.slice(idx + 1)]
            } else {
              messages.value = [...messages.value, msg]
            }
          }
          break

        case 'done':
          {
            const sources = event.sources || []
            const toolsUsed = event.tools_used || []
            const idx = messages.value.findIndex((m) => m.id === assistantId)
            if (idx >= 0) {
              const updated = [...messages.value]
              updated[idx] = {
                ...updated[idx],
                sources,
                toolsUsed,
                content: fullAnswer || updated[idx].content,
              }
              messages.value = updated
            }
          }
          break

        case 'error':
          console.error('流式错误:', event.content)
          {
            const idx = messages.value.findIndex((m) => m.id === assistantId)
            if (idx >= 0) {
              const updated = [...messages.value]
              updated[idx] = { ...updated[idx], content: `抱歉，发生了错误：${event.content}` }
              messages.value = updated
            } else {
              messages.value = [...messages.value, {
                id: assistantId,
                role: 'assistant',
                content: `抱歉，发生了错误：${event.content}`,
                timestamp: new Date(),
              }]
            }
          }
          break
      }
    }, sessionId.value)

    await refreshSessionList()
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value = [...messages.value, {
      id: assistantId,
      role: 'assistant',
      content: '抱歉，发生了错误。请稍后再试。',
      timestamp: new Date(),
    }]
  } finally {
    loading.value = false
    thinkingStatus.value = ''
  }
}

async function handleUpload(file: File) {
  uploading.value = true
  try {
    const response = await uploadDocument(file)
    console.log('上传成功:', response)
    await fetchDocumentCount()
    alert(`文档上传成功！共 ${response.chunks_count} 个文档块`)
  } catch (error) {
    console.error('上传失败:', error)
    alert('文档上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

async function handleClear() {
  if (confirm('确定要清空知识库吗？')) {
    try {
      await clearDocuments()
      await fetchDocumentCount()
      alert('知识库已清空')
    } catch (error) {
      console.error('清空失败:', error)
      alert('清空失败，请重试')
    }
  }
}
</script>

<template>
  <div class="h-screen flex flex-col bg-gray-100">
    <!-- 顶部栏 -->
    <header class="bg-blue-600 text-white p-3 shadow-lg flex-shrink-0">
      <h1 class="text-lg font-bold text-center">Agentic RAG 智能问答系统</h1>
    </header>

    <!-- 主体：侧边栏 + 聊天区 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 左侧会话列表 -->
      <SessionSidebar
        :sessions="sessions"
        :active-session-id="sessionId"
        @select="switchToSession"
        @new="handleNewChat"
        @delete="handleDeleteSession"
      />

      <!-- 右侧内容区 -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto p-4">
          <div class="max-w-4xl mx-auto">
            <!-- 文档上传区 -->
            <div class="mb-4">
              <DocumentUpload
                :uploading="uploading"
                :document-count="documentCount"
                @upload="handleUpload"
                @clear="handleClear"
              />
            </div>

            <!-- 聊天区 -->
            <div class="bg-white rounded-lg shadow-md flex flex-col h-[500px]">
              <ChatPanel
                :messages="messages"
                :loading="loading"
                :thinking-status="thinkingStatus"
              />
              <ChatInput
                :disabled="loading"
                @send="handleSend"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>