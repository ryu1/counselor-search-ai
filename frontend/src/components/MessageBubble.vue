<template>
  <div class="message-bubble" :class="['bubble', message.role]">
    <div class="avatar">
      {{ message.role === 'user' ? 'U' : 'A' }}
    </div>
    <div class="message-text" v-html="renderedContent"></div>
    <div class="message-meta">
      {{ message.timestamp }}
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {marked} from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  message: {
    id: number
    role: 'user' | 'assistant'
    content: string
    timestamp: string
  }
}>()

const renderedContent = computed(() => {
  const html = marked.parse(props.message.content) as string
  return DOMPurify.sanitize(html)
})
</script>

<style scoped>
.message-bubble {
  margin-bottom: 1rem;
  max-width: 80%;
}

.message-bubble.user {
  justify-self: flex-end;
}

.message-bubble.assistant {
  justify-self: flex-start;
}

.avatar {
  font-size: 0.75rem;
  margin-right: 0.5rem;
  min-width: 1.5rem;
  text-align: center;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: 12px 12px 2px 12px;
  font-size: 0.875rem;
  line-height: 1.4;
}

.bubble.user .message-text {
  background-color: #e94560;
  color: white;
  border-radius: 12px 12px 12px 2px;
  margin-left: auto;
}

.bubble.assistant .message-text {
  background-color: #f1f5f9;
  color: #1e293b;
  border-radius: 12px 12px 12px 2px;
  margin-right: auto;
}

.message-meta {
  font-size: 0.65rem;
  opacity: 0.5;
  margin-top: 0.25rem;
  text-align: right;
}

.bubble.user .message-meta {
  text-align: right;
}

.bubble.assistant .message-meta {
  text-align: left;
}

.bubble.user {
  align-self: flex-end;
}

.bubble.assistant {
  align-self: flex-start;
}
</style>
