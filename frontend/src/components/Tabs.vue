<script setup>
defineProps({ tabs: Array })
const model = defineModel()
</script>

<template>
  <div class="tabs">
    <button v-for="(t, i) in tabs" :key="t" :class="{ active: Number(model) === i }" @click="model = i">{{ t }}</button>
  </div>
</template>
