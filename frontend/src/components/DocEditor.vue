<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import { autosize, debounce, get, put } from '../api'

// markdown=true — показ отрендеренного текста с кнопкой «Изменить» (планы)
const props = defineProps({ docKey: String, placeholder: String, markdown: Boolean })
const md = new MarkdownIt({ breaks: true, linkify: true })
const text = ref('')
const editing = ref(!props.markdown)
const area = ref(null)

const save = debounce((key, value) => put(`/docs/${key}`, { text: value }))

watch(
  () => props.docKey,
  async (key) => {
    save.flush()
    text.value = (await get(`/docs/${key}`)).text
    await nextTick()
    if (area.value) autosize(area.value)
  },
  { immediate: true },
)

function input(e) {
  autosize(e)
  save(props.docKey, text.value)
}

async function edit() {
  editing.value = true
  await nextTick()
  autosize(area.value)
  area.value.focus()
}

function done() {
  save.flush()
  editing.value = false
}

onBeforeUnmount(save.flush)
</script>

<template>
  <div class="doc">
    <template v-if="editing">
      <textarea ref="area" v-model="text" class="doc-area" :placeholder="placeholder" @input="input" />
      <button v-if="markdown" class="btn" @click="done">Готово</button>
    </template>
    <template v-else>
      <div v-if="text.trim()" class="md" v-html="md.render(text)" />
      <p v-else class="muted">{{ placeholder }}</p>
      <button class="btn" @click="edit">Изменить</button>
    </template>
  </div>
</template>
