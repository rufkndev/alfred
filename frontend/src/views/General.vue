<script setup>
import { computed } from 'vue'
import { addDays, formatDay, today } from '../api'
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import TaskList from '../components/TaskList.vue'
import DayBlocks from '../components/DayBlocks.vue'
import DocEditor from '../components/DocEditor.vue'
import NoteList from '../components/NoteList.vue'

const date = useQuery('d', today)
const tab = useQuery('tab', 0)
const isToday = computed(() => date.value === today())
</script>

<template>
  <Page title="Общее" chat="general" memory="memory:general" memory-title="Память · Общее">
    <Tabs v-model="tab" :tabs="['Задачи', 'Блоки', 'Мысли', 'Заметки']" />
    <div v-if="tab == 1 || tab == 2" class="day-switch">
      <button class="top-btn" @click="date = addDays(date, -1)">‹</button>
      <button class="day-label" @click="date = today()">{{ isToday ? 'Сегодня, ' : '' }}{{ formatDay(date) }}</button>
      <button class="top-btn" @click="date = addDays(date, 1)">›</button>
    </div>
    <TaskList v-if="tab == 0" />
    <DayBlocks v-else-if="tab == 1" :date="date" />
    <DocEditor v-else-if="tab == 2" :doc-key="`thoughts:${date}`" placeholder="Мысли и заметки за день…" />
    <NoteList v-else list="general" />
  </Page>
</template>
