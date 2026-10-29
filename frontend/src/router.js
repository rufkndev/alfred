import { computed } from 'vue'
import { createRouter, createWebHistory, useRoute, useRouter } from 'vue-router'
import General from './views/General.vue'
import Economy from './views/Economy.vue'
import Admission from './views/Admission.vue'
import Business from './views/Business.vue'
import BusinessItem from './views/BusinessItem.vue'
import Skill from './views/Skill.vue'
import Plan from './views/Plan.vue'
import ChatView from './views/ChatView.vue'
import DocView from './views/DocView.vue'
import NoteView from './views/NoteView.vue'
import Settings from './views/Settings.vue'
import CustomSection from './views/CustomSection.vue'
import NewSection from './views/NewSection.vue'
import BlockTemplate from './views/BlockTemplate.vue'
import { state } from './api'

export const SECTIONS = [
  { path: '/', title: 'Общее', chat: 'general' },
  { path: '/economy', title: 'Экономика', chat: 'economy' },
  { path: '/admission', title: 'Поступление', chat: 'admission' },
  { path: '/business', title: 'Бизнес', chat: 'business' },
  { path: '/basketball', title: 'Баскетбол', chat: 'basketball' },
  { path: '/cs2', title: 'CS2', chat: 'cs2' },
  { path: '/gym', title: 'Зал', chat: 'gym' },
  { path: '/food', title: 'Питание', chat: 'food' },
]

export const TAB_TITLES = { tasks: 'Задачи', notes: 'Заметки', mindsets: 'Установки', plan: 'План' }

// Встроенные разделы + свои (ключ чата своего раздела — s<id>)
export const allSections = () =>
  SECTIONS.concat(state.sections.map((s) => ({ path: `/s/${s.id}`, title: s.title, chat: `s${s.id}` })))

export const chatTitle = (chat) => allSections().find((s) => s.chat === chat)?.title

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: General },
    { path: '/economy', component: Economy },
    { path: '/admission', component: Admission },
    { path: '/business', component: Business },
    { path: '/business/:id', component: BusinessItem, props: true },
    { path: '/basketball', component: Skill, props: { section: 'basketball' } },
    { path: '/cs2', component: Skill, props: { section: 'cs2' } },
    { path: '/gym', component: Plan, props: { section: 'gym' } },
    { path: '/food', component: Plan, props: { section: 'food' } },
    { path: '/chat/:chat', component: ChatView, props: true },
    { path: '/doc/:key(.*)', component: DocView, props: (r) => ({ docKey: r.params.key, title: r.query.title }) },
    { path: '/notes/:id', component: NoteView, props: true },
    { path: '/settings', component: Settings },
    { path: '/s/:id', component: CustomSection, props: true },
    { path: '/sections/new', component: NewSection },
    { path: '/blocks/template', component: BlockTemplate },
  ],
})

// Состояние в query-параметре, чтобы вкладка/дата сохранялись при возврате назад
export function useQuery(name, fallback) {
  const route = useRoute()
  const router = useRouter()
  return computed({
    get: () => route.query[name] ?? (typeof fallback === 'function' ? fallback() : fallback),
    set: (v) => router.replace({ query: { ...route.query, [name]: v } }),
  })
}
