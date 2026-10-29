<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loadSections, post } from '../api'
import { TAB_TITLES } from '../router'
import Page from '../components/Page.vue'

const router = useRouter()
const title = ref('')
const tabs = ref(['tasks', 'notes'])

async function create() {
  if (!title.value.trim()) return
  const section = await post('/sections', { title: title.value.trim(), tabs: tabs.value })
  await loadSections()
  router.replace(`/s/${section.id}`)
}
</script>

<template>
  <Page title="Новый раздел" back="/">
    <form class="form" @submit.prevent="create">
      <input v-model="title" placeholder="Название" />
      <label v-for="(name, tab) in TAB_TITLES" :key="tab" class="check-row">
        <input v-model="tabs" type="checkbox" :value="tab" />
        {{ name }}
      </label>
      <p class="hint">Чат с ИИ и память есть в каждом разделе.</p>
      <button class="btn primary" type="submit">Создать</button>
    </form>
  </Page>
</template>
