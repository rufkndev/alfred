<script setup>
import { onMounted } from 'vue'
import { get, state } from './api'
import LockScreen from './components/LockScreen.vue'

const LOCK_AFTER = 3 * 60 * 1000

const expired = () => Date.now() - Number(localStorage.getItem('hiddenAt') || 0) > LOCK_AFTER

document.addEventListener('visibilitychange', () => {
  if (document.hidden) localStorage.setItem('hiddenAt', Date.now())
  else if (expired()) state.locked = true
})

onMounted(async () => {
  Object.assign(state, await get('/auth/status'))
  state.locked = !state.authed || expired()
  state.ready = true
})
</script>

<template>
  <template v-if="state.ready">
    <LockScreen v-if="state.locked || !state.authed" />
    <router-view v-else />
  </template>
</template>
