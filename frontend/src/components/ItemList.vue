<script setup>
import { ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { del, get, patch, post, q } from '../api'

// archive=true — режим установок (архив вместо галочки); plain=true — без галочек (шаблон блоков)
const props = defineProps({
  list: String,
  date: String,
  archive: Boolean,
  plain: Boolean,
  placeholder: { type: String, default: 'Добавить' },
})
const flag = props.archive ? 'archived' : 'done'
const open = ref([])
const closed = ref([])
const showClosed = ref(false)
const text = ref('')

async function load() {
  const items = await get(`/items?list=${q(props.list)}` + (props.date ? `&date=${props.date}` : ''))
  open.value = items.filter((i) => !i[flag])
  closed.value = items.filter((i) => i[flag])
}
watch(() => [props.list, props.date], load, { immediate: true })

async function add() {
  const value = text.value.trim()
  if (!value) return
  text.value = ''
  open.value.push(await post('/items', { list: props.list, date: props.date, text: value }))
}

async function toggle(item) {
  await patch(`/items/${item.id}`, { [flag]: !item[flag] })
  await load()
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

const reorder = () => post('/items/reorder', { ids: open.value.map((i) => i.id) })
</script>

<template>
  <div class="list">
    <draggable v-model="open" item-key="id" handle=".handle" :animation="150" @end="reorder">
      <template #item="{ element: item }">
        <div class="row top">
          <button v-if="!archive && !plain" class="check" @click="toggle(item)" />
          <textarea v-autosize class="row-text" rows="1" :value="item.text" @change="save(item, $event)" @keydown.enter.prevent="$event.target.blur()" />
          <button v-if="archive" class="row-action" @click="toggle(item)">в архив</button>
          <span class="handle">⋮⋮</span>
        </div>
      </template>
    </draggable>

    <div class="row">
      <span class="plus">+</span>
      <input v-model="text" class="row-input" :placeholder="placeholder" enterkeyhint="done" @keydown.enter="add" @blur="add" />
    </div>

    <template v-if="closed.length">
      <button class="closed-toggle" @click="showClosed = !showClosed">
        {{ archive ? 'Архив' : 'Выполнено' }} · {{ closed.length }} {{ showClosed ? '▴' : '▾' }}
      </button>
      <template v-if="showClosed">
        <div v-for="item in closed" :key="item.id" class="row top done">
          <button v-if="!archive" class="check on" @click="toggle(item)" />
          <textarea v-autosize class="row-text" rows="1" :value="item.text" @change="save(item, $event)" @keydown.enter.prevent="$event.target.blur()" />
          <button v-if="archive" class="row-action" @click="toggle(item)">вернуть</button>
        </div>
      </template>
    </template>
    <p class="hint">Чтобы удалить — сотри текст.</p>
  </div>
</template>
