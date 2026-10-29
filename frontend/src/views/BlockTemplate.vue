<script setup>
import { today } from '../api'
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import ItemList from '../components/ItemList.vue'

// Постоянные блоки по дням недели: каждый день они появляются в «Общем → Блоки» сами
const weekday = new Date(today() + 'T12:00:00Z').getUTCDay() || 7
const tab = useQuery('wd', weekday - 1)
</script>

<template>
  <Page title="Шаблон блоков" back="/?tab=1">
    <Tabs v-model="tab" :tabs="['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']" />
    <ItemList :list="`blocks_wd${Number(tab) + 1}`" plain placeholder="Добавить постоянный блок" />
    <p class="hint">Эти блоки каждую неделю появляются в этот день сами, галочки у каждого дня свои.</p>
  </Page>
</template>
