<template>
  <div class="min-h-screen counselor-app">
    <header class="counselor-header">
      <div class="container">
        <h1 class="counselor-title">カウンセラー検索 AI</h1>
        <p class="counselor-subtitle">希望条件でカウンセラーを検索します</p>
      </div>
    </header>

    <main class="container py-6">
      <ChatView/>
    </main>
  </div>
</template>

<script setup lang="ts">
import ChatView from '@/components/ChatView.vue'
</script>

<style scoped>
.counselor-app {
  font-family: 'Inter', sans-serif;
}

.counselor-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  padding: 2rem 0;
}

.counselor-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.counselor-subtitle {
  font-size: 1rem;
  opacity: 0.8;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}
</style>