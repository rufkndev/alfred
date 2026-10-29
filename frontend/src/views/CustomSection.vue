<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { del, loadSections, patch, state } from '../api'
import { TAB_TITLES, useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import ItemList from '../components/ItemList.vue'
import TaskList from '../components/TaskList.vue'
import NoteList from '../components/NoteList.vue'
import DocEditor from '../components/DocEditor.vue'

// Раздел, созданный в приложении: вкладки выбраны при создании, чат и память есть всегда
const props = defineProps({ id: String })
const router = useRouter()
const tab = useQuery('tab', 0)
const section = computed(() => state.sections.find((s) => s.id == props.id))
const key = computed(() => `s${props.id}`)
const current = computed(() => section.value?.tabs[tab.value])

async function rename() {
  const title = prompt('Название раздела', section.value.title)?.trim()
  if (!title) return
  await patch(`/sections/${props.id}`, { title })
  loadSections()
}

async function remove() {
  if (!confirm(`Удалить «${section.value.title}» со всеми задачами, заметками, памятью и чатом? Это нельзя отменить.`)) return
  await del(`/sections/${props.id}`)
  await loadSections()
  router.replace('/')
}
</script>

<template>
  <Page :title="section?.title" :chat="key" :memory="`memory:${key}`" :memory-title="`Память · ${section?.title || ''}`">
    <template v-if="section">
      <Tabs v-if="section.tabs.length > 1" v-model="tab" :tabs="section.tabs.map((t) => TAB_TITLES[t])" />
      <TaskList v-if="current === 'tasks'" :list="`${key}_tasks`" />
      <NoteList v-else-if="current === 'notes'" :list="key" />
      <ItemList v-else-if="current === 'mindsets'" :list="`${key}_mindsets`" archive placeholder="Добавить установку" />
      <DocEditor v-else-if="current === 'plan'" :doc-key="`plan:${key}`" markdown placeholder="План пока пуст — обсуди его в чате." />
      <p v-if="!section.tabs.length" class="hint">В этом разделе только чат с ИИ и память.</p>
      <button class="btn subtle" @click="rename">Переименовать</button>
      <button class="btn subtle danger" @click="remove">Удалить раздел</button>
    </template>
  </Page>
</template>
