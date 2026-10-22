<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SECTIONS } from '../router'

const props = defineProps({ title: String, back: String, chat: String, memory: String, memoryTitle: String })
const menu = ref(false)
const route = useRoute()
const router = useRouter()

function goBack() {
  if (window.history.state?.back) router.back()
  else router.push(props.back)
}
</script>

<template>
  <div class="page">
    <header class="top">
      <button v-if="back" class="top-btn" @click="goBack">‹</button>
      <button v-else class="top-btn" @click="menu = true">☰</button>
      <div class="top-title">{{ title }}</div>
      <div class="top-right">
        <slot name="right">
          <router-link v-if="memory" class="link" :to="{ path: `/doc/${memory}`, query: { title: memoryTitle || 'Память' } }">
            Память
          </router-link>
        </slot>
      </div>
    </header>

    <main class="content"><slot /></main>

    <router-link v-if="chat" class="fab" :to="`/chat/${chat}`" aria-label="Чат">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">
        <path d="M4 5h16v11H9l-5 4z" />
      </svg>
    </router-link>

    <div v-if="menu" class="menu">
      <div class="top">
        <button class="top-btn" @click="menu = false">✕</button>
        <div class="top-title">Alfred</div>
        <div class="top-right" />
      </div>
      <nav>
        <router-link v-for="s in SECTIONS" :key="s.path" :to="s.path" :class="{ active: route.path === s.path }" @click="menu = false">
          {{ s.title }}
        </router-link>
        <router-link to="/settings" class="muted" @click="menu = false">Настройки</router-link>
      </nav>
    </div>
  </div>
</template>
