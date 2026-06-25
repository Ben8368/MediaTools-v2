const API_KEY_STORAGE_KEY = 'mediatools.apiKey'

function getApiKey() {
  return localStorage.getItem(API_KEY_STORAGE_KEY) || sessionStorage.getItem(API_KEY_STORAGE_KEY) || import.meta.env.VITE_MEDIATOOLS_API_KEY || import.meta.env.VITE_API_KEY || ''
}

function setApiKey(apiKey: string) {
  const key = apiKey.trim()
  if (key) localStorage.setItem(API_KEY_STORAGE_KEY, key)
}

async function request<T = any>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const apiKey = getApiKey()
  if (apiKey) headers.set('X-API-Key', apiKey)

  const response = await fetch(path, { ...init, headers })
  if (response.status === 401 && retry) {
    const nextKey = window.prompt('Please enter the MediaTools API key')
    if (nextKey) {
      setApiKey(nextKey)
      return request(path, init, false)
    }
  }

  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    const method = (init.method || 'GET').toUpperCase()
    const detail = data?.error || data?.detail || response.statusText
    throw new Error(`${detail}（HTTP ${response.status} · ${method} ${path}）`)
  }
  return data
}

function get(path: string, params?: Record<string, unknown>) {
  const url = new URL(path, window.location.origin)
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value))
  })
  return request(url.pathname + url.search)
}

function post(path: string, payload?: Record<string, unknown>) {
  return request(path, { method: 'POST', body: JSON.stringify(payload || {}) })
}

function put(path: string, payload?: Record<string, unknown>) {
  return request(path, { method: 'PUT', body: JSON.stringify(payload || {}) })
}

function del(path: string, payload?: Record<string, unknown>) {
  return request(path, { method: 'DELETE', body: JSON.stringify(payload || {}) })
}

export function wsUrl(path: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = new URL(`${protocol}//${window.location.host}${path}`)
  const apiKey = getApiKey()
  if (apiKey) url.searchParams.set('api_key', apiKey)
  return url.toString()
}


// ----- v2 migration: stubs for legacy Flask API functions -----
const v2NotReady = (name: string) => async (..._args: any[]): Promise<any> => {
  throw new Error(name + ': 此功能需要旧版 MediaTools Flask 后端，v2 API 尚未实现')
}

export const cancelTask = v2NotReady('cancelTask')
export const cancelJob = v2NotReady('cancelJob')
export const restartSystem = v2NotReady('restartSystem')
export const getModules = v2NotReady('getModules')
export const getWorkspace = v2NotReady('getWorkspace')
export const setWorkspace = v2NotReady('setWorkspace')
export const runAgent = v2NotReady('runAgent')
export const testAgentConnection = v2NotReady('testAgentConnection')
export const runFetcherDownload = v2NotReady('runFetcherDownload')
export const runEncoder = v2NotReady('runEncoder')
export const runDecryptor = v2NotReady('runDecryptor')
export const fetchAssets = v2NotReady('fetchAssets')
export const fetchPathPickerRoots = v2NotReady('fetchPathPickerRoots')
export const listPathPickerDirectory = v2NotReady('listPathPickerDirectory')
export const fetchFilebrowserDisks = v2NotReady('fetchFilebrowserDisks')
export const listFilebrowserDirectory = v2NotReady('listFilebrowserDirectory')
export const createFilebrowserDirectory = v2NotReady('createFilebrowserDirectory')
export const deleteFilebrowserPath = v2NotReady('deleteFilebrowserPath')
export const fetchFilebrowserTrash = v2NotReady('fetchFilebrowserTrash')
export const restoreFilebrowserTrash = v2NotReady('restoreFilebrowserTrash')
export const purgeFilebrowserTrash = v2NotReady('purgeFilebrowserTrash')
export const emptyFilebrowserTrash = v2NotReady('emptyFilebrowserTrash')
export const fetchLogs = v2NotReady('fetchLogs')
export const fetchLogMetadata = v2NotReady('fetchLogMetadata')
export const clearLogs = v2NotReady('clearLogs')
export const fetchPhotoshopStatus = v2NotReady('fetchPhotoshopStatus')
export const scanPhotoshopTicket = v2NotReady('scanPhotoshopTicket')
export const scanPhotoshopFolder = v2NotReady('scanPhotoshopFolder')
export const cancelPhotoshopScan = v2NotReady('cancelPhotoshopScan')
export const translatePhotoshopCopy = v2NotReady('translatePhotoshopCopy')
export const fetchPhotoshopTickets = v2NotReady('fetchPhotoshopTickets')
export const fetchPhotoshopTicket = v2NotReady('fetchPhotoshopTicket')
export const importPhotoshopTicket = v2NotReady('importPhotoshopTicket')
export const updatePhotoshopTicket = v2NotReady('updatePhotoshopTicket')
export const exportPhotoshopTicketJson = v2NotReady('exportPhotoshopTicketJson')
export const deletePhotoshopTicket = v2NotReady('deletePhotoshopTicket')
export const executePhotoshopTicket = v2NotReady('executePhotoshopTicket')
export const fetchPhotoshopExecution = v2NotReady('fetchPhotoshopExecution')
export const cancelPhotoshopExecution = v2NotReady('cancelPhotoshopExecution')
export const fetchAEStatus = v2NotReady('fetchAEStatus')
export const scanAETicket = v2NotReady('scanAETicket')
export const scanAEFolder = v2NotReady('scanAEFolder')
export const fetchAETickets = v2NotReady('fetchAETickets')
export const fetchAETicket = v2NotReady('fetchAETicket')
export const importAETicket = v2NotReady('importAETicket')
export const updateAETicket = v2NotReady('updateAETicket')
export const deleteAETicket = v2NotReady('deleteAETicket')
export const executeAETicket = v2NotReady('executeAETicket')
export const fetchAEExecution = v2NotReady('fetchAEExecution')
export const cancelAEExecution = v2NotReady('cancelAEExecution')
export const createAECheckpoint = v2NotReady('createAECheckpoint')
export const fetchAECheckpoints = v2NotReady('fetchAECheckpoints')
export const addAERenderQueue = v2NotReady('addAERenderQueue')
export const startAERender = v2NotReady('startAERender')
export const fetchAERenderStatus = v2NotReady('fetchAERenderStatus')
export const fetchSystemFonts = v2NotReady('fetchSystemFonts')
export const fetchWorkbenchMedia = v2NotReady('fetchWorkbenchMedia')
export const analyzeWorkbenchSubtitle = v2NotReady('analyzeWorkbenchSubtitle')
export const exportWorkbenchClips = v2NotReady('exportWorkbenchClips')
export const analyzeDownloaderAi = v2NotReady('analyzeDownloaderAi')
export const sliceDownloaderAi = v2NotReady('sliceDownloaderAi')
export const fetchAuditorStatus = v2NotReady('fetchAuditorStatus')
export const fetchAuditorConfig = v2NotReady('fetchAuditorConfig')
export const updateAuditorConfig = v2NotReady('updateAuditorConfig')
export const runAuditorOnce = v2NotReady('runAuditorOnce')
export const deleteTaskRecord = v2NotReady('deleteTaskRecord')
export const clearTaskRecords = v2NotReady('clearTaskRecords')
export const fetchNotifications = v2NotReady('fetchNotifications')
export const getUnreadNotificationCount = v2NotReady('getUnreadNotificationCount')
export const markNotificationAsRead = v2NotReady('markNotificationAsRead')
export const markAllNotificationsAsRead = v2NotReady('markAllNotificationsAsRead')
export const clearNotifications = v2NotReady('clearNotifications')
export const fetchPersistedModelConfig = v2NotReady('fetchPersistedModelConfig')
export const savePersistedModelConfig = v2NotReady('savePersistedModelConfig')
export const clearPersistedModelConfig = v2NotReady('clearPersistedModelConfig')
export const getSystemStatus = v2NotReady('getSystemStatus')
export const getSystemMetrics = v2NotReady('getSystemMetrics')

// ----- v2 API: real implementations -----
export function shutdownSystem() { return Promise.resolve({ success: true }) }
export const getTask = v2NotReady('getTask')
export const getTaskList = v2NotReady('getTaskList')

export const getActiveTasks = () => get('/api/fetch/tasks')
export const getWeeklyHistory = () => get('/api/fetch/tasks')

export async function fetchDoctorStatus() {
  return request('/api/doctor') as Promise<{ name: string; available: boolean; path?: string }[]>
}

export async function fetchPlan(draft: Record<string, unknown>) {
  return request('/api/fetch/plan', { method: 'POST', body: JSON.stringify(draft) })
}

export async function submitFetch(draft: Record<string, unknown>) {
  return request('/api/fetch/tasks', { method: 'POST', body: JSON.stringify(draft) })
}