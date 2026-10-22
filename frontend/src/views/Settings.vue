<script setup>
import { ref } from 'vue'
import { startRegistration } from '@simplewebauthn/browser'
import { get, post, state } from '../api'
import Page from '../components/Page.vue'

const message = ref('')
const pushOn = ref(typeof Notification !== 'undefined' && Notification.permission === 'granted')

async function run(fn) {
  message.value = ''
  try {
    await fn()
  } catch (e) {
    message.value = e.message
  }
}

const enableFaceId = () =>
  run(async () => {
    const optionsJSON = await post('/auth/webauthn/register/options')
    await post('/auth/webauthn/register/verify', await startRegistration({ optionsJSON }))
    state.faceid = true
    message.value = 'Face ID включён'
  })

const enablePush = () =>
  run(async () => {
    if (!('PushManager' in window)) throw new Error('Открой Alfred с иконки на экране «Домой» (iOS 16.4+)')
    if ((await Notification.requestPermission()) !== 'granted') throw new Error('Уведомления запрещены в настройках iPhone')
    const reg = await navigator.serviceWorker.ready
    const { key } = await get('/push/key')
    const raw = atob(key.replace(/-/g, '+').replace(/_/g, '/'))
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: Uint8Array.from(raw, (c) => c.charCodeAt(0)),
    })
    await post('/push/subscribe', sub.toJSON())
    pushOn.value = true
    message.value = 'Уведомления включены'
  })

const testPush = () => run(() => post('/push/test'))

const logout = () =>
  run(async () => {
    await post('/auth/logout')
    state.authed = false
    state.locked = true
  })
</script>

<template>
  <Page title="Настройки" back="/">
    <div class="list">
      <button class="nav-row" @click="enableFaceId">
        Face ID <span class="muted">{{ state.faceid ? 'включён · добавить ещё' : 'включить' }}</span>
      </button>
      <button class="nav-row" @click="enablePush">
        Уведомления <span class="muted">{{ pushOn ? 'включены · обновить' : 'включить' }}</span>
      </button>
      <button v-if="pushOn" class="nav-row" @click="testPush">Тестовое уведомление <span class="muted">›</span></button>
      <button class="nav-row danger" @click="logout">Выйти</button>
    </div>
    <p class="hint">{{ message }}</p>
  </Page>
</template>
