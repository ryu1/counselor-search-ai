<template>
  <div class="input-area">
    <textarea
      v-model="inputText"
      class="textarea-input"
      placeholder="カウンセラー検索の希望条件を入力 (例: 新宿駅から近くて、女性のカウンセラーにオンラインで土曜14時ごろ相談したい)"
      :disabled="isSearching"
      rows="3"
    ></textarea>

    <div class="action-buttons">
      <button
        @click="submitSearch"
        :disabled="!inputText.trim() || isSearching"
        class="btn-primary"
      >
        {{ isSearching ? '検索中...' : '検索実行' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from 'vue'

const emit = defineEmits<{
  submit: [text: string]
}>()

const inputText = ref('')
const isSearching = ref(false)

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
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.textarea-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  resize: vertical;
  transition: border-color 0.2s;
}

.textarea-input:focus {
  outline: none;
  border-color: #e94560;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
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
