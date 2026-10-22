<script setup>
import { onMounted, ref } from 'vue'
import { get, patch } from '../api'
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import ItemList from '../components/ItemList.vue'
import NoteList from '../components/NoteList.vue'

const props = defineProps({ id: String })
const biz = ref(null)
const tab = useQuery('tab', 0)

onMounted(async () => (biz.value = (await get('/businesses')).find((b) => b.id == props.id)))

async function toggleArchive() {
  biz.value = await patch(`/businesses/${props.id}`, { archived: !biz.value.archived })
}
</script>

<template>
  <Page :title="biz?.name" back="/business" chat="business" :memory="`memory:biz:${id}`" :memory-title="`Память · ${biz?.name || ''}`">
    <Tabs v-model="tab" :tabs="['Задачи', 'Заметки']" />
    <ItemList v-if="tab == 0" :list="`biz:${id}:tasks`" placeholder="Добавить задачу" />
    <NoteList v-else :list="`biz:${id}`" />
    <button v-if="biz" class="btn subtle" @click="toggleArchive">{{ biz.archived ? 'Вернуть из архива' : 'В архив' }}</button>
  </Page>
</template>
