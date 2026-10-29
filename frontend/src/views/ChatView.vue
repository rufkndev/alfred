<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { autosize, get, post } from '../api'
import { allSections, chatTitle } from '../router'

const props = defineProps({ chat: String })
const router = useRouter()
const md = new MarkdownIt({ breaks: true, linkify: true })
const messages = ref([])
const text = ref('')
const busy = ref(false)
const error = ref('')
const box = ref(null)
const input = ref(null)
let timer = null
let alive = true

const visible = computed(() =>
  messages.value.filter((m) => m.role === 'user' || (m.role === 'assistant' && m.content) || (m.role === 'tool' && m.meta?.label)),
)

async function scroll() {
  await nextTick()
  if (box.value) box.value.scrollTop = box.value.scrollHeight
}

// Ответ готовится на сервере в фоне: пока он не готов, опрашиваем раз в 1,5 секунды
async function load() {
  clearTimeout(timer)
  const r = await get(`/chat/${props.chat}`)
  const grew = r.messages.length !== messages.value.length
  messages.value = r.messages
  busy.value = r.busy
  if (r.error) error.value = r.error
  if (grew) scroll()
  clearTimeout(timer)
  if (r.busy && alive) timer = setTimeout(load, 1500)
}

const onVisible = () => !document.hidden && load()

onMounted(() => {
  load()
  document.addEventListener('visibilitychange', onVisible)
})

onBeforeUnmount(() => {
  alive = false
  clearTimeout(timer)
  document.removeEventListener('visibilitychange', onVisible)
})

function back() {
  if (window.history.state?.back) router.back()
  else router.push(allSections().find((s) => s.chat === props.chat)?.path || '/')
}

async function send() {
  const value = text.value.trim()
  if (!value || busy.value) return
  text.value = ''
  await nextTick()
  autosize(input.value)
  error.value = ''
  busy.value = true
  messages.value.push({ id: 'pending', role: 'user', content: value })
  scroll()
  try {
    await post(`/chat/${props.chat}`, { text: value })
  } catch (e) {
    error.value = e.message
  }
  load()
}

async function reset() {
  if (!confirm('Начать новый диалог? Старая переписка останется в базе.')) return
  await post(`/chat/${props.chat}/reset`)
  messages.value = []
}
</script>

<template>
  <div class="chat">
    <header class="top">
      <button class="top-btn" @click="back">‹</button>
      <div class="top-title">Чат · {{ chatTitle(chat) }}</div>
      <div class="top-right"><button class="link" @click="reset">Новый</button></div>
    </header>

    <div ref="box" class="chat-messages">
      <p v-if="!visible.length" class="muted chat-empty">Новый диалог</p>
      <template v-for="m in visible" :key="m.id">
        <div v-if="m.role === 'user'" class="bubble user">{{ m.content }}</div>
        <div v-else-if="m.role === 'tool'" class="tool-line">✓ {{ m.meta.label }}</div>
        <div v-else class="bubble ai md" v-html="md.render(m.content)" />
      </template>
      <div v-if="busy" class="bubble ai typing">…</div>
      <div v-if="error" class="chat-error">{{ error }}</div>
    </div>

    <form class="composer" @submit.prevent="send">
      <textarea ref="input" v-model="text" rows="1" placeholder="Сообщение" @input="autosize" />
      <button class="send" type="submit" :disabled="busy || !text.trim()">↑</button>
    </form>
  </div>
</template>
