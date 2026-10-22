<script setup>
import { chatTitle, useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import ItemList from '../components/ItemList.vue'
import NoteList from '../components/NoteList.vue'

// Баскетбол и CS2: материалы, мысли, установки
const props = defineProps({ section: String })
const title = chatTitle(props.section)
const tab = useQuery('tab', 0)
</script>

<template>
  <Page :title="title" :chat="section" :memory="`memory:${section}`" :memory-title="`Память · ${title}`">
    <Tabs v-model="tab" :tabs="['Материалы', 'Мысли', 'Установки']" />
    <NoteList v-if="tab == 0" :list="`${section}_materials`" />
    <NoteList v-else-if="tab == 1" :list="`${section}_thoughts`" />
    <ItemList v-else :list="`${section}_mindsets`" archive placeholder="Добавить установку" />
  </Page>
</template>
