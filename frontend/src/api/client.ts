import { ref, onMounted, onBeforeUnmount } from 'vue'

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

type ChatState = {
  messages: Message[]
  isSearching: boolean
  currentResults: SearchResult[]
  error: string | null
}

// モックデータ（開発用 / バックエンド未接続時）
const MOCK_SEARCH_RESULTS: SearchResult[] = [
  {
    office_id: '1',
    office_name: '新宿オフィス',
    nearest_stations: '新宿駅',
    method: 'オンライン',
    gender: '女性',
    age: '30代',
    expertise: 'うつ',
  },
  {
    office_id: '2',
    office_name: '渋谷オフィス',
    nearest_stations: '渋谷駅',
    method: '対面',
    gender: '男性',
    age: '40代',
    expertise: 'ストレス',
  },
]

type SearchResponse = {
  success: boolean
  result?: {
    count: number
    results: SearchResult[]
  }
  error?: {
    code: string
    message: string
  }
}

export const useChatStore = () => {
  const state = ref<ChatState>({
    messages: [],
    isSearching: false,
    currentResults: [],
    error: null,
  })

  // モック応答を返すかどうかのフラグ
  const useMock = ref(false)

  const API_URL = import.meta.env.VITE_API_URL || '/api/search'

  const sendMessage = async (text: string) => {
    state.value.isSearching = true
    state.value.error = null

    try {
      // 開発環境ではモックを使用、本番では実際のAPIを呼び出し
      const isDevelopment = import.meta.env.DEV
      let response: SearchResponse

      if (isDevelopment && useMock.value) {
        // モックデータを使用
        response = {
          success: true,
          result: {
            count: MOCK_SEARCH_RESULTS.length,
            results: MOCK_SEARCH_RESULTS,
          },
        }
      } else {
        // 実際のAPIコール
        response = await fetch(API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: text }),
        }).then(async (res) => {
          if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            return { success: false, error: { code: 'API_ERROR', message: errorData.detail || 'Search failed' } }
          }
          return res.json()
        })
      }

      if (!response.success) {
        throw new Error(response.error?.message || 'Search failed')
      }

      state.value.messages.push({
        id: Date.now(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      })

      if (response.result?.answer) {
        state.value.messages.push({
          id: Date.now(),
          role: 'assistant',
          content: response.result.answer,
          timestamp: new Date().toISOString(),
        })
      }

      if (response.result?.results) {
        state.value.currentResults = response.result.results
      }
    } catch (err) {
      console.error('Search error:', err)
      state.value.error = err instanceof Error ? err.message : 'An error occurred'
      state.value.messages.push({
        id: Date.now(),
        role: 'assistant',
        content: `エラー: ${state.value.error}`,
        timestamp: new Date().toISOString(),
      })
    } finally {
      state.value.isSearching = false
    }
  }

  const clearResults = () => {
    state.value.currentResults = []
    state.value.error = null
  }

  return { state, sendMessage, clearResults, useMock }
}