<script setup>
import Page from '../components/Page.vue'
import DocEditor from '../components/DocEditor.vue'

defineProps({ docKey: String, title: String })
</script>

<template>
  <Page :title="title || 'Документ'" back="/">
    <p class="hint">Альфред сам дополняет память. Можно вставить сюда стартовую информацию или поправить вручную.</p>
    <DocEditor :doc-key="docKey" placeholder="Пусто" />
  </Page>
</template>
