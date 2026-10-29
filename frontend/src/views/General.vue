<script setup>
import { computed } from 'vue'
import { addDays, formatDay, today } from '../api'
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import ItemList from '../components/ItemList.vue'
import DocEditor from '../components/DocEditor.vue'
import NoteList from '../components/NoteList.vue'

const date = useQuery('d', today)
const tab = useQuery('tab', 0)
const isToday = computed(() => date.value === today())
</script>

<template>
  <Page title="Общее" chat="general" memory="memory:general" memory-title="Память · Общее">
    <div v-if="tab != 3" class="day-switch">
      <button class="top-btn" @click="date = addDays(date, -1)">‹</button>
      <button class="day-label" @click="date = today()">{{ isToday ? 'Сегодня, ' : '' }}{{ formatDay(date) }}</button>
      <button class="top-btn" @click="date = addDays(date, 1)">›</button>
    </div>
    <Tabs v-model="tab" :tabs="['Задачи', 'Блоки', 'Мысли', 'Заметки']" />
    <ItemList v-if="tab == 0" list="day_tasks" :date="date" placeholder="Добавить задачу" />
    <ItemList v-else-if="tab == 1" list="day_blocks" :date="date" placeholder="Добавить блок" />
    <DocEditor v-else-if="tab == 2" :doc-key="`thoughts:${date}`" placeholder="Мысли и заметки за день…" />
    <NoteList v-else list="general" />
  </Page>
</template>
