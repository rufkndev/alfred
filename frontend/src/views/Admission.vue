<script setup>
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import TaskList from '../components/TaskList.vue'
import NoteList from '../components/NoteList.vue'

const tab = useQuery('tab', 0)
</script>

<template>
  <Page title="Поступление" chat="admission" memory="memory:admission" memory-title="Память · Поступление">
    <Tabs v-model="tab" :tabs="['Задачи', 'Заметки']" />
    <TaskList v-if="tab == 0" list="admission_tasks" />
    <NoteList v-else list="admission" />
  </Page>
</template>
