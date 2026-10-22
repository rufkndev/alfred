<script setup>
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import ItemList from '../components/ItemList.vue'
import NoteList from '../components/NoteList.vue'

const tab = useQuery('tab', 0)
</script>

<template>
  <Page title="Поступление" chat="admission" memory="memory:admission" memory-title="Память · Поступление">
    <Tabs v-model="tab" :tabs="['Задачи', 'Заметки']" />
    <ItemList v-if="tab == 0" list="admission_tasks" placeholder="Добавить задачу" />
    <NoteList v-else list="admission" />
  </Page>
</template>
