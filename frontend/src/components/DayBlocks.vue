<script setup>
import { ref, watch } from 'vue'
import { get, post } from '../api'
import ItemList from './ItemList.vue'

// Блоки дня: постоянные из шаблона дня недели (галочки свои на каждый день) + разовые на эту дату
const props = defineProps({ date: String })
const template = ref([])

const load = async () => (template.value = await get(`/blocks?date=${props.date}`))
watch(() => props.date, load, { immediate: true })

async function toggle(block) {
  block.done = !block.done
  await post('/blocks/done', { date: props.date, item_id: block.id, done: block.done })
}
</script>

<template>
  <div>
    <div class="list">
      <div v-for="b in template" :key="b.id" class="row top" :class="{ done: b.done }">
        <button class="check" :class="{ on: b.done }" @click="toggle(b)" />
        <div class="row-text static">{{ b.text }}</div>
      </div>
    </div>
    <div v-if="template.length" class="section-label">Разовые на этот день</div>
    <ItemList list="day_blocks" :date="date" placeholder="Добавить блок на этот день" />
    <router-link to="/blocks/template" class="nav-row">Шаблон недели <span class="muted">›</span></router-link>
  </div>
</template>
