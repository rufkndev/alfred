<script setup>
import { computed, onMounted, ref } from 'vue'
import { get, post } from '../api'
import Page from '../components/Page.vue'

const businesses = ref([])
const name = ref('')
const active = computed(() => businesses.value.filter((b) => !b.archived))
const archived = computed(() => businesses.value.filter((b) => b.archived))

onMounted(async () => (businesses.value = await get('/businesses')))

async function add() {
  const value = name.value.trim()
  if (!value) return
  name.value = ''
  businesses.value.push(await post('/businesses', { name: value }))
}
</script>

<template>
  <Page title="Бизнес" chat="business" memory="memory:business" memory-title="Память · Бизнес">
    <div class="list">
      <router-link v-for="b in active" :key="b.id" :to="`/business/${b.id}`" class="nav-row">{{ b.name }} <span class="muted">›</span></router-link>
      <div class="row">
        <span class="plus">+</span>
        <input v-model="name" class="row-input" placeholder="Новый бизнес" enterkeyhint="done" @keydown.enter="add" />
      </div>
      <template v-if="archived.length">
        <div class="section-label">Архив</div>
        <router-link v-for="b in archived" :key="b.id" :to="`/business/${b.id}`" class="nav-row muted">{{ b.name }} <span>›</span></router-link>
      </template>
    </div>
  </Page>
</template>
