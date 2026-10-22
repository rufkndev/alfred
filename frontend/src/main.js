import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
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

createApp(App).use(router).mount('#app')
