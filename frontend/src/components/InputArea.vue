<template>
  <div class="input-area">
    <div v-if="quickReplies.length > 0" class="quick-replies">
      <button
        v-for="reply in quickReplies"
        :key="reply"
        @click="selectQuickReply(reply)"
        class="quick-reply-btn"
        :disabled="isSearching"
      >
        {{ reply }}
      </button>
    </div>

    <div class="input-row">
      <textarea
        v-model="inputText"
        class="textarea-input"
        :placeholder="placeholder"
        :disabled="isSearching"
        rows="2"
        @keydown.enter.prevent="submitSearch"
      ></textarea>

      <div class="action-buttons">
        <button
          @click="submitSearch"
          :disabled="!inputText.trim() || isSearching"
          class="btn-primary"
        >
          {{ isSearching ? '検索中...' : '送信' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, watch} from 'vue'
import {useChatStore} from '../stores/chat'

const chatStore = useChatStore()

const emit = defineEmits<{
  submit: [text: string]
}>()

const inputText = ref('')
const isSearching = ref(false)

const quickReplies = computed(() => {
  const messages = chatStore.messages
  if (messages.length === 0) return []

  const lastMessage = messages[messages.length - 1]
  if (lastMessage.role !== 'assistant') return []

  const content = lastMessage.content

  if (content.includes('咨询方式')) {
    return ['オンライン', '対面', '電話', 'メール', '指定なし']
  }
  if (content.includes('车站') || content.includes('地区')) {
    return ['新宿駅', '立川駅', '池袋駅', '渋谷駅', '品川駅', '東京駅', '秋葉原駅', '中野駅', '吉祥寺駅', '水道橋駅', '溜池山王駅', '新橋駅', '指定なし']
  }
  if (content.includes('性别')) {
    return ['男性', '女性', '指定なし']
  }
  return []
})

const placeholder = computed(() => {
  if (quickReplies.value.length > 0) {
    return '選択肢から選ぶか、テキストで入力してください'
  }
  return '相談したいことを入力してください'
})

const selectQuickReply = (reply: string) => {
  inputText.value = reply
  submitSearch()
}

const submitSearch = async () => {
  if (!inputText.value.trim() || isSearching.value) return

  isSearching.value = true
  const text = inputText.value.trim()

  emit('submit', text)

  inputText.value = ''
  isSearching.value = false
}
</script>

<style scoped>
.input-area {
  padding: 1rem;
  background-color: #1a1a2e;
  border-top: 1px solid #2d2d44;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.quick-reply-btn {
  padding: 0.5rem 1rem;
  background-color: #2d2d44;
  color: #e94560;
  border: 1px solid #e94560;
  border-radius: 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-reply-btn:hover:not(:disabled) {
  background-color: #e94560;
  color: white;
}

.quick-reply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-row {
  display: flex;
  gap: 0.5rem;
}

.textarea-input {
  flex: 1;
  padding: 0.75rem 1rem;
  background-color: #0f0f23;
  border: 1px solid #2d2d44;
  border-radius: 8px;
  color: #f1f1f1;
  font-size: 1rem;
  resize: none;
  transition: border-color 0.2s;
}

.textarea-input:focus {
  outline: none;
  border-color: #e94560;
}

.textarea-input::placeholder {
  color: #6b7280;
}

.action-buttons {
  display: flex;
  align-items: flex-end;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background-color: #e94560;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background-color: #d53f5c;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
