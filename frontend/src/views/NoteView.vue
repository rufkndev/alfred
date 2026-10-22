<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { autosize, debounce, del, get, patch } from '../api'
import Page from '../components/Page.vue'

const props = defineProps({ id: String })
const router = useRouter()
const note = ref(null)
const area = ref(null)
let removed = false

const save = debounce(() => patch(`/notes/${props.id}`, { title: note.value.title, body: note.value.body }))

onMounted(async () => {
  note.value = await get(`/notes/${props.id}`)
  await nextTick()
  autosize(area.value)
})

onBeforeUnmount(() => {
  if (!note.value || removed) return
  if (!note.value.title.trim() && !note.value.body.trim()) del(`/notes/${props.id}`)
  else save.flush()
})

async function remove() {
  if (!confirm('Удалить заметку?')) return
  removed = true
  await del(`/notes/${props.id}`)
  router.back()
}
</script>

<template>
  <Page title="" back="/">
    <template #right><button class="link danger" @click="remove">Удалить</button></template>
    <template v-if="note">
      <input v-model="note.title" class="note-title-input" placeholder="Заголовок" @input="save" />
      <textarea ref="area" v-model="note.body" class="doc-area" placeholder="Текст" @input="(e) => (autosize(e), save())" />
    </template>
  </Page>
</template>
