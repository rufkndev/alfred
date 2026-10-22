<script setup>
import { computed, onMounted, ref } from 'vue'
import { formatDateTime, get, money, patch, post } from '../api'

const accounts = ref([])
const openId = ref(null)
const amount = ref('')
const adding = ref(null)

const load = async () => (accounts.value = await get('/accounts'))
onMounted(load)

const total = computed(() => accounts.value.reduce((s, a) => s + Number(a.amount), 0))
const num = (v) => Number(String(v).replace(/\s/g, '').replace(',', '.'))

function toggle(a) {
  openId.value = openId.value === a.id ? null : a.id
  amount.value = ''
}

async function update(a) {
  if (amount.value === '') return
  await post(`/accounts/${a.id}/balance`, { amount: num(amount.value) })
  amount.value = ''
  load()
}

async function archive(a) {
  if (!confirm(`Убрать «${a.name}»?`)) return
  await patch(`/accounts/${a.id}`, { archived: true })
  load()
}

async function add() {
  if (!adding.value.name.trim()) return
  await post('/accounts', { name: adding.value.name.trim(), amount: num(adding.value.amount || 0) })
  adding.value = null
  load()
}
</script>

<template>
  <div>
    <div class="summary">Всего {{ money(total) }}</div>

    <form v-if="adding" class="form" @submit.prevent="add">
      <input v-model="adding.name" placeholder="Где (карта, наличные, вклад…)" />
      <input v-model="adding.amount" placeholder="Сумма, ₽" inputmode="decimal" />
      <div class="form-row">
        <button class="btn primary" type="submit">Добавить</button>
        <button class="btn" type="button" @click="adding = null">Отмена</button>
      </div>
    </form>

    <div class="list">
      <button v-if="!adding" class="row add-row" @click="adding = { name: '', amount: '' }"><span class="plus">+</span>Добавить</button>
      <div v-for="a in accounts" :key="a.id">
        <button class="money-row" @click="toggle(a)">
          <div>{{ a.name }}</div>
          <div>{{ money(a.amount) }}</div>
        </button>
        <div v-if="openId === a.id" class="form">
          <form class="form-row" @submit.prevent="update(a)">
            <input v-model="amount" placeholder="Новая сумма" inputmode="decimal" />
            <button class="btn primary" type="submit">Обновить</button>
          </form>
          <div v-for="(h, i) in a.history" :key="i" class="history">
            <span class="muted">{{ formatDateTime(h.created_at) }}</span>
            <span>{{ money(h.amount) }}</span>
          </div>
          <button class="btn danger" @click="archive(a)">Убрать счёт</button>
        </div>
      </div>
    </div>
  </div>
</template>
