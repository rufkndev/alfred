<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { formatDateTime, get, post, q } from '../api'

const props = defineProps({ list: String })
const notes = ref([])
const router = useRouter()

watch(() => props.list, async () => (notes.value = await get(`/notes?list=${q(props.list)}`)), { immediate: true })

async function create() {
  const note = await post('/notes', { list: props.list, title: '', body: '' })
  router.push(`/notes/${note.id}`)
}
</script>

<template>
  <div class="list">
    <button class="row add-row" @click="create"><span class="plus">+</span>Новая заметка</button>
    <router-link v-for="n in notes" :key="n.id" :to="`/notes/${n.id}`" class="note-row">
      <div class="note-title">{{ n.title || 'Без названия' }}</div>
      <div class="note-meta">{{ formatDateTime(n.updated_at) }} · {{ n.body.slice(0, 60) || 'пусто' }}</div>
    </router-link>
  </div>
</template>
