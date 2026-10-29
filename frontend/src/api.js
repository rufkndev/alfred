import { reactive } from 'vue'

export const state = reactive({ ready: false, authed: false, locked: true, faceid: false, tz: 'Europe/Moscow', sections: [] })

async function api(path, method = 'GET', body) {
  const r = await fetch('/api' + path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (r.status === 401) {
    state.authed = false
    state.locked = true
  }
  const data = (r.headers.get('content-type') || '').includes('json') ? await r.json() : null
  if (!r.ok) throw new Error(data?.detail || r.statusText)
  return data
}

export const get = (p) => api(p)
export const post = (p, b = {}) => api(p, 'POST', b)
export const patch = (p, b) => api(p, 'PATCH', b)
export const put = (p, b) => api(p, 'PUT', b)
export const del = (p) => api(p, 'DELETE')

export const q = (s) => encodeURIComponent(s)

// Свои разделы, созданные в приложении
export const loadSections = async () => (state.sections = await get('/sections'))

// Даты в формате YYYY-MM-DD по часовому поясу приложения
export function today() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: state.tz }).format(new Date())
}

export function addDays(iso, n) {
  const d = new Date(iso + 'T12:00:00Z')
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}

export function formatDay(iso) {
  return new Date(iso + 'T12:00:00Z').toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' })
}

export function formatDateTime(s) {
  return new Date(s).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: state.tz })
}

export const money = (n) => Math.round(Number(n)).toLocaleString('ru-RU') + ' ₽'

export function debounce(fn, ms = 500) {
  let t
  const d = (...args) => {
    clearTimeout(t)
    t = setTimeout(() => {
      t = null
      fn(...args)
    }, ms)
    d.args = args
  }
  d.flush = () => {
    if (t) {
      clearTimeout(t)
      t = null
      fn(...d.args)
    }
  }
  return d
}

export function autosize(e) {
  const el = e.target || e
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}
