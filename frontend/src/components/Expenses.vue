<script setup>
import { computed, ref, watch } from 'vue'
import { del, get, money, patch, post } from '../api'

const props = defineProps({ kind: String })
const UNITS = {
  day: { every: 'каждый день', short: 'дн.', perMonth: 30.44 },
  week: { every: 'каждую неделю', short: 'нед.', perMonth: 4.345 },
  month: { every: 'каждый месяц', short: 'мес.', perMonth: 1 },
}
const items = ref([])
const form = ref(null)

const load = async () => (items.value = await get(`/expenses?kind=${props.kind}`))
watch(() => props.kind, load, { immediate: true })

const perMonth = (e) => (Number(e.amount) * UNITS[e.unit].perMonth) / e.every_n
const total = computed(() => items.value.reduce((s, e) => s + perMonth(e), 0))
const period = (e) => (e.every_n == 1 ? UNITS[e.unit].every : `раз в ${e.every_n} ${UNITS[e.unit].short}`)

function edit(e) {
  form.value = e ? { ...e } : { kind: props.kind, name: '', amount: '', every_n: 1, unit: 'month', note: '' }
}

async function save() {
  const f = form.value
  if (!f.name.trim() || !f.amount) return
  const data = { ...f, amount: Number(String(f.amount).replace(',', '.')), every_n: Number(f.every_n) || 1 }
  if (f.id) await patch(`/expenses/${f.id}`, data)
  else await post('/expenses', data)
  form.value = null
  load()
}

async function remove() {
  if (!confirm('Удалить?')) return
  await del(`/expenses/${form.value.id}`)
  form.value = null
  load()
}
</script>

<template>
  <div>
    <div class="summary">≈ {{ money(total) }} в месяц</div>

    <form v-if="form" class="form" @submit.prevent="save">
      <input v-model="form.name" placeholder="Название" />
      <input v-model="form.amount" placeholder="Сумма, ₽" inputmode="decimal" />
      <div class="form-row">
        <span>Раз в</span>
        <input v-model="form.every_n" class="num" inputmode="numeric" />
        <select v-model="form.unit">
          <option value="day">дней</option>
          <option value="week">недель</option>
          <option value="month">месяцев</option>
        </select>
      </div>
      <input v-model="form.note" placeholder="Заметка" />
      <div class="form-row">
        <button class="btn primary" type="submit">Сохранить</button>
        <button class="btn" type="button" @click="form = null">Отмена</button>
        <button v-if="form.id" class="btn danger" type="button" @click="remove">Удалить</button>
      </div>
    </form>

    <div class="list">
      <button v-if="!form" class="row add-row" @click="edit()"><span class="plus">+</span>Добавить</button>
      <button v-for="e in items" :key="e.id" class="money-row" @click="edit(e)">
        <div>
          <div>{{ e.name }}</div>
          <div class="note-meta">{{ money(e.amount) }} · {{ period(e) }}{{ e.note ? ' · ' + e.note : '' }}</div>
        </div>
        <div class="muted">{{ money(perMonth(e)) }}/мес</div>
      </button>
    </div>
  </div>
</template>
