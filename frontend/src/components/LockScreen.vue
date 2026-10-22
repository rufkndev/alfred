<script setup>
import { onMounted, ref } from 'vue'
import { startAuthentication } from '@simplewebauthn/browser'
import { post, state } from '../api'

const pin = ref('')
const error = ref('')
const busy = ref(false)

function unlock() {
  state.authed = true
  state.locked = false
  localStorage.setItem('hiddenAt', Date.now())
}

async function faceId() {
  error.value = ''
  try {
    const optionsJSON = await post('/auth/webauthn/login/options')
    await post('/auth/webauthn/login/verify', await startAuthentication({ optionsJSON }))
    unlock()
  } catch (e) {
    if (e.name !== 'NotAllowedError') error.value = e.message
  }
}

async function press(d) {
  if (busy.value || pin.value.length >= 4) return
  error.value = ''
  pin.value += d
  if (pin.value.length < 4) return
  busy.value = true
  try {
    await post('/auth/pin', { pin: pin.value })
    unlock()
  } catch (e) {
    error.value = e.message
    pin.value = ''
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  if (state.faceid) faceId()
})
</script>

<template>
  <div class="lock">
    <div class="lock-title">Alfred</div>
    <div class="dots">
      <span v-for="i in 4" :key="i" :class="{ on: pin.length >= i }" />
    </div>
    <div class="lock-error">{{ error }}</div>
    <div class="pad">
      <button v-for="d in [1, 2, 3, 4, 5, 6, 7, 8, 9]" :key="d" @click="press(String(d))">{{ d }}</button>
      <button v-if="state.faceid" class="pad-text" @click="faceId">Face ID</button>
      <span v-else />
      <button @click="press('0')">0</button>
      <button class="pad-text" @click="pin = pin.slice(0, -1)">⌫</button>
    </div>
  </div>
</template>

<style scoped>
.lock {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}
.lock-title {
  font-size: 22px;
  font-weight: 600;
}
.dots {
  display: flex;
  gap: 16px;
}
.dots span {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 1.5px solid var(--text);
}
.dots span.on {
  background: var(--text);
}
.lock-error {
  min-height: 20px;
  color: var(--danger);
  font-size: 14px;
}
.pad {
  display: grid;
  grid-template-columns: repeat(3, 76px);
  gap: 16px 24px;
}
.pad button {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  background: var(--soft);
  font-size: 28px;
  text-align: center;
}
.pad .pad-text {
  background: none;
  font-size: 16px;
}
</style>
