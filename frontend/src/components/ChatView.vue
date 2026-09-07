<template>
  <div class="chat-view">
    <section class="chat-history" id="chat-history">
      <div v-for="message in messages" :key="message.id" class="message-bubble">
        <MessageBubble :message="message"/>
      </div>
    </section>

    <input-area @submit="handleSubmit"/>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageBubble from '@/components/MessageBubble.vue'
import InputArea from '@/components/InputArea.vue'

const chatStore = useChatStore()

const messages = computed(() => chatStore.messages)
const isSearching = computed(() => chatStore.isSearching)
const currentResults = computed(() => chatStore.currentResults)
const error = computed(() => chatStore.error)

const handleSubmit = async (text: string) => {
  await chatStore.sendSearch(text)
}
</script>

<style scoped>
.chat-view {
  height: 600px;
  display: flex;
  flex-direction: column;
  background-color: #0f0f23;
}

.chat-history {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  color: #f1f1f1;
}

.message-bubble {
  margin-bottom: 0.75rem;
  max-width: 80%;
}

@media (max-width: 768px) {
  .message-bubble {
    max-width: 90%;
  }
}
</style>