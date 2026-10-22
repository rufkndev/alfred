<script setup>
import { chatTitle } from '../router'
import Page from '../components/Page.vue'
import DocEditor from '../components/DocEditor.vue'

// Зал и питание: план, который ведёт ИИ
const props = defineProps({ section: String })
const title = chatTitle(props.section)
</script>

<template>
  <Page :title="title" :chat="section" :memory="`memory:${section}`" :memory-title="`Память · ${title}`">
    <DocEditor :doc-key="`plan:${section}`" markdown placeholder="План пока пуст — обсуди его в чате, и Альфред его составит." />
  </Page>
</template>
