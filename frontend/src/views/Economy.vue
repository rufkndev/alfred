<script setup>
import { useQuery } from '../router'
import Page from '../components/Page.vue'
import Tabs from '../components/Tabs.vue'
import Expenses from '../components/Expenses.vue'
import Accounts from '../components/Accounts.vue'

const tab = useQuery('tab', 0)
</script>

<template>
  <Page title="Экономика" chat="economy" memory="memory:economy" memory-title="Память · Экономика">
    <Tabs v-model="tab" :tabs="['Регулярные', 'Подписки', 'Счета']" />
    <Expenses v-if="tab == 0" kind="regular" />
    <Expenses v-else-if="tab == 1" kind="subscription" />
    <Accounts v-else />
  </Page>
</template>
