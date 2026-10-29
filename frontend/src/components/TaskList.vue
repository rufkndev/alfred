<script setup>
import { computed, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { addDays, del, formatDay, get, patch, post, q, today } from '../api'

// Задачи с датами по группам Сегодня / Завтра / Позже / Без даты.
// list — задачи одного раздела; без list — сводка «Общего» (свои задачи + задачи разделов с датой)
const props = defineProps({ list: String })
const items = ref([])
const showDone = ref(false)
const text = ref('')

const t = today()
const tomorrow = addDays(t, 1)

async function load() {
  items.value = await get(props.list ? `/tasks?list=${q(props.list)}` : '/tasks')
}
watch(() => props.list, load, { immediate: true })

const groups = computed(() => {
  const open = items.value.filter((i) => !i.done)
  return [
    { title: 'Сегодня', items: open.filter((i) => i.date && i.date <= t) },
    { title: 'Завтра', items: open.filter((i) => i.date === tomorrow) },
    { title: 'Позже', items: open.filter((i) => i.date > tomorrow).sort((a, b) => a.date.localeCompare(b.date)) },
    { title: 'Без даты', items: open.filter((i) => !i.date) },
  ].filter((g) => g.items.length)
})
const done = computed(() => items.value.filter((i) => i.done))

function dateLabel(date) {
  if (!date) return '+ дата'
  if (date === t) return 'сегодня'
  if (date === tomorrow) return 'завтра'
  return formatDay(date)
}

async function add() {
  const value = text.value.trim()
  if (!value) return
  text.value = ''
  await post('/items', { list: props.list || 'day_tasks', date: props.list ? null : t, text: value })
  load()
}

async function toggle(item) {
  await patch(`/items/${item.id}`, { done: !item.done })
  load()
}

async function setDate(item, e) {
  await patch(`/items/${item.id}`, { date: e.target.value || null })
  load()
}

async function save(item, e) {
  const value = e.target.value.trim()
  if (value === item.text) return
  if (!value) {
    await del(`/items/${item.id}`)
    return load()
  }
  item.text = value
  await patch(`/items/${item.id}`, { text: value })
}

const reorder = (group) => post('/items/reorder', { ids: group.items.map((i) => i.id) })
</script>

<template>
  <div class="list">
    <div class="row">
      <span class="plus">+</span>
      <input v-model="text" class="row-input" :placeholder="list ? 'Добавить задачу' : 'Добавить задачу на сегодня'" enterkeyhint="done" @keydown.enter="add" @blur="add" />
    </div>

    <template v-for="g in groups" :key="g.title">
      <div class="section-label">{{ g.title }}</div>
      <draggable :list="g.items" item-key="id" handle=".handle" :animation="150" @end="reorder(g)">
        <template #item="{ element: item }">
          <div class="row top">
            <button class="check" @click="toggle(item)" />
            <div class="task-body">
              <textarea v-autosize class="row-text" rows="1" :value="item.text" @change="save(item, $event)" @keydown.enter.prevent="$event.target.blur()" />
              <div class="task-meta">
                <label class="date-chip" :class="{ overdue: item.date && item.date < t }">
                  {{ dateLabel(item.date) }}
                  <input type="date" :value="item.date || ''" @change="setDate(item, $event)" />
                </label>
                <span v-if="item.source">· {{ item.source }}</span>
              </div>
            </div>
            <span class="handle">⋮⋮</span>
          </div>
        </template>
      </draggable>
    </template>

    <template v-if="done.length">
      <button class="closed-toggle" @click="showDone = !showDone">Выполнено · {{ done.length }} {{ showDone ? '▴' : '▾' }}</button>
      <template v-if="showDone">
        <div v-for="item in done" :key="item.id" class="row top done">
          <button class="check on" @click="toggle(item)" />
          <div class="task-body">
            <textarea v-autosize class="row-text" rows="1" :value="item.text" @change="save(item, $event)" @keydown.enter.prevent="$event.target.blur()" />
            <div v-if="item.source" class="task-meta">{{ item.source }}</div>
          </div>
        </div>
      </template>
    </template>
    <p class="hint">Дата — нажми на метку под задачей. Чтобы удалить — сотри текст.</p>
  </div>
</template>
