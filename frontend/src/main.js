import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { autosize } from './api'
import './style.css'

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js')

// Видимая область с учётом клавиатуры iOS (нужна чату)
const vv = window.visualViewport
const setViewport = () => {
  document.documentElement.style.setProperty('--app-h', (vv?.height || window.innerHeight) + 'px')
  document.documentElement.style.setProperty('--app-top', (vv?.offsetTop || 0) + 'px')
}
vv?.addEventListener('resize', setViewport)
vv?.addEventListener('scroll', setViewport)
setViewport()

// v-autosize: textarea растёт по тексту, длинные задачи переносятся, а не обрезаются
const autosizeDirective = {
  mounted(el) {
    autosize(el)
    el.addEventListener('input', () => autosize(el))
  },
  updated: autosize,
}

createApp(App).use(router).directive('autosize', autosizeDirective).mount('#app')
