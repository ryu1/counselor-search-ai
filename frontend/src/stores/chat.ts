import { defineStore } from 'pinia'
import { ref } from 'vue'

type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isSearching = ref(false)
  const error = ref<string | null>(null)
  const sessionId = ref<string | null>(null)
  const actorId = ref<string | null>(null)

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    messages.value.push({
      id: Date.now(),
      role,
      content,
      timestamp: new Date().toISOString(),
    })
    // Auto-scroll to bottom
    setTimeout(() => {
      const chatHistory = document.getElementById('chat-history') as HTMLElement
      if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight
      }
    }, 100)
  }

  const API_URL = import.meta.env.VITE_API_URL || '/api/search'

  const sendSearch = async (text: string) => {
    isSearching.value = true
    error.value = null
    addMessage('user', text)

    try {
      // actor_idがなければ生成（最初のリクエスト時）
      if (!actorId.value) {
        actorId.value = `actor_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
      }

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: text,
          session_id: sessionId.value,
          actor_id: actorId.value,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Search failed')
      }

      const result = await response.json()

      // Session ID を保存
      if (result.session_id) {
        sessionId.value = result.session_id
      }

      if (result.result?.answer) {
        addMessage('assistant', result.result.answer)
      }
    } catch (err) {
      console.error('Search error:', err)
      error.value = err instanceof Error ? err.message : 'An error occurred'
      addMessage('assistant', `エラー: ${error.value}`)
    } finally {
      isSearching.value = false
    }
  }

  const clearChat = () => {
    messages.value = []
    error.value = null
    sessionId.value = null
    actorId.value = null
  }

  return { messages, isSearching, error, sessionId, actorId, addMessage, sendSearch, clearChat }
})