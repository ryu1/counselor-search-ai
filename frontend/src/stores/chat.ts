import { defineStore } from 'pinia'
import { ref } from 'vue'

type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

type SearchResult = {
  office_id: string
  office_name: string
  nearest_stations: string
  method: string
  gender: string
  age: string
  expertise: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isSearching = ref(false)
  const currentResults = ref<SearchResult[]>([])
  const error = ref<string | null>(null)

  const addMessage = (role: string, content: string) => {
    messages.value.push({
      id: Date.now(),
      role,
      content,
      timestamp: new Date().toISOString(),
    })
    // Auto-scroll to bottom
    const chatHistory = document.getElementById('chat-history') as HTMLElement
    if (chatHistory) {
      chatHistory.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const API_URL = import.meta.env.VITE_API_URL || '/api/search'

  const sendSearch = async (text: string) => {
    isSearching.value = true
    error.value = null
    addMessage('user', text)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: text }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Search failed')
      }

      const result = await response.json()

      if (result.result?.answer) {
        addMessage('assistant', result.result.answer)
      }

      if (result.result?.results) {
        currentResults.value = result.result.results
      }
    } catch (err) {
      console.error('Search error:', err)
      error.value = err instanceof Error ? err.message : 'An error occurred'
      addMessage('assistant', `エラー: ${error.value}`)
    } finally {
      isSearching.value = false
    }
  }

  const clearResults = () => {
    currentResults.value = []
    error.value = null
  }

  return { messages, isSearching, currentResults, error, addMessage, sendSearch, clearResults }
})