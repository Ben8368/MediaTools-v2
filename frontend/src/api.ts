const API_KEY_STORAGE_KEY = 'mediatools.apiKey'

type DoctorTool = {
  name: string
  available: boolean
  path?: string | null
}

type ApiTask = {
  id?: string
  task_id?: string
  title?: string
  source_url?: string
  status?: string
  progress?: number
  stage?: string
  created_at?: number
  updated_at?: number | null
  started_at?: number | null
  completed_at?: number | null
  error?: string | null
}

type SystemMetricsPayload = {
  runtime?: {
    uptime_seconds?: number
  }
  system?: {
    cpu_percent?: number
    memory_percent?: number
    gpu_percent?: number
    gpu_available?: boolean
    gpu_detail?: string
  }
  network?: {
    upload?: { text?: string }
    download?: { text?: string }
    upload_bytes_per_sec?: number
    download_bytes_per_sec?: number
  }
}

type LogQuery = {
  level?: string
  module?: string
  page?: number
  page_size?: number
}

const TERMINAL_TASK_STATUSES = new Set(['completed', 'failed', 'cancelled', 'partial'])
const ACTIVE_TASK_STATUSES = new Set(['pending', 'running', 'paused'])

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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let data: any = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }
  if (!response.ok) {
    const method = (init.method || 'GET').toUpperCase()
    const detail = data?.error || data?.detail || response.statusText
    throw new Error(`${detail}（HTTP ${response.status} · ${method} ${path}）`)
  }
  return data as T
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

// ----- v2 API: implemented endpoints -----

export async function fetchDoctorStatus() {
  return request('/api/doctor') as Promise<{ name: string; available: boolean; path?: string }[]>
}

export async function fetchSystemRuntimeMetrics() {
  return request('/api/system/metrics') as Promise<SystemMetricsPayload>
}

export async function fetchPlan(draft: Record<string, unknown>) {
  return request('/api/fetch/plan', { method: 'POST', body: JSON.stringify(draft) })
}

export async function submitFetch(draft: Record<string, unknown>) {
  return request('/api/fetch/tasks', { method: 'POST', body: JSON.stringify(draft) })
}

export const getActiveTasks = () => get('/api/fetch/tasks')
export const getWeeklyHistory = () => get('/api/fetch/tasks')
export const cancelTask = (taskId: string) => post(`/api/fetch/tasks/${encodeURIComponent(taskId)}/cancel`)
export const deleteTaskRecord = (taskId: string) => del(`/api/fetch/tasks/${encodeURIComponent(taskId)}`)
export const clearTaskRecords = (taskIds?: string[]) => del('/api/fetch/tasks', { task_ids: taskIds || [] })

function normalizeTaskList(response: unknown): ApiTask[] {
  if (Array.isArray(response)) return response as ApiTask[]
  if (response && typeof response === 'object' && Array.isArray((response as { tasks?: unknown }).tasks)) {
    return (response as { tasks: ApiTask[] }).tasks
  }
  return []
}

function normalizeProgress(value: unknown) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 0
  return value <= 1 ? value * 100 : value
}

function taskStatusLabel(status: string) {
  if (status === 'pending') return '等待中'
  if (status === 'running') return '进行中'
  if (status === 'paused') return '已暂停'
  if (status === 'cancelled') return '已取消'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'partial') return '部分完成'
  return status
}

function serviceFromTool(id: string, name: string, tool?: DoctorTool) {
  const online = Boolean(tool?.available)
  return {
    id,
    name,
    online,
    status: online ? 'ready' : 'missing',
    runtime_status: online ? 'online' : 'offline',
    availability_status: online ? 'ready' : 'missing',
    detail: online ? (tool?.path || 'available') : `${tool?.name || name} not found on PATH`,
    dep: tool?.name || null,
  }
}

function servicesFromDoctor(tools: DoctorTool[]) {
  const byName = new Map(tools.map((tool) => [tool.name, tool]))
  return [
    serviceFromTool('fetcher', '下载服务', byName.get('yt-dlp')),
    serviceFromTool('encoder', '编码转码', byName.get('ffmpeg')),
  ]
}

function systemTasksFromApi(tasks: ApiTask[]) {
  return tasks
    .filter((task) => ACTIVE_TASK_STATUSES.has(String(task.status || 'pending')))
    .map((task) => {
      const status = String(task.status || 'pending')
      return {
        id: task.id || task.task_id || '',
        name: task.title || 'Media download',
        source: task.source_url || task.title || '',
        type: 'download',
        status,
        status_label: taskStatusLabel(status),
        stage: task.stage || 'queued',
        progress: normalizeProgress(task.progress),
        can_pause: false,
        can_resume: false,
        can_cancel: status === 'pending' || status === 'running',
      }
    })
}

function timestampToLogTime(timestamp?: number | null) {
  if (!timestamp) return new Date().toISOString().replace('T', ' ').slice(0, 19)
  return new Date(timestamp * 1000).toISOString().replace('T', ' ').slice(0, 19)
}

function taskLogLevel(status: string) {
  if (status === 'failed' || status === 'partial') return 'ERROR'
  if (status === 'cancelled') return 'WARNING'
  return 'NOTICE'
}

function taskLogEvent(task: ApiTask) {
  const status = String(task.status || 'pending')
  const title = task.title || task.source_url || task.id || task.task_id || '下载任务'
  if (task.error) return `${title}: ${task.error}`
  return `${title}: ${taskStatusLabel(status)}${task.stage ? ` · ${task.stage}` : ''}`
}

function taskLogsFromApi(tasks: ApiTask[]) {
  return tasks
    .map((task) => {
      const status = String(task.status || 'pending')
      return {
        level: taskLogLevel(status),
        module: 'tasks',
        time: timestampToLogTime(task.updated_at || task.created_at),
        user: 'system',
        event: taskLogEvent(task),
        message: taskLogEvent(task),
      }
    })
    .sort((a, b) => b.time.localeCompare(a.time))
}

function emptyLogResponse(query: LogQuery = {}) {
  const page = Number(query.page || 1)
  const pageSize = Number(query.page_size || 50)
  return { ok: true, total: 0, items: [], page, page_size: pageSize, levels: ['NOTICE', 'WARNING', 'ERROR', 'CRITICAL'] }
}

export async function getSystemMetrics() {
  const [doctorResult, tasksResult, systemResult] = await Promise.allSettled([
    fetchDoctorStatus(),
    getActiveTasks(),
    fetchSystemRuntimeMetrics(),
  ])
  const tools = doctorResult.status === 'fulfilled' && Array.isArray(doctorResult.value) ? doctorResult.value as DoctorTool[] : []
  const allTasks = tasksResult.status === 'fulfilled' ? normalizeTaskList(tasksResult.value) : []
  const runtimeMetrics = systemResult.status === 'fulfilled' ? systemResult.value : {}
  const activeTasks = systemTasksFromApi(allTasks)

  return {
    runtime: runtimeMetrics.runtime || { uptime_seconds: 0 },
    system: runtimeMetrics.system || { cpu_percent: 0, memory_percent: 0, gpu_percent: 0, gpu_available: false, gpu_detail: 'v2 轻前端暂未采集 GPU 指标' },
    network: runtimeMetrics.network || { upload: { text: '0 B/s' }, download: { text: '0 B/s' }, upload_bytes_per_sec: 0, download_bytes_per_sec: 0 },
    services: servicesFromDoctor(tools),
    tasks: activeTasks,
    task_summary: {
      active_downloads: activeTasks.length,
      total_download_records: allTasks.length,
      terminal_download_records: allTasks.filter((task) => TERMINAL_TASK_STATUSES.has(String(task.status || ''))).length,
    },
    log_mode: import.meta.env.DEV ? 'development' : 'production',
  }
}

export async function fetchLogs(query: LogQuery = {}) {
  try {
    const tasks = normalizeTaskList(await getActiveTasks())
    const level = String(query.level || '')
    const moduleName = String(query.module || '')
    const page = Math.max(1, Number(query.page || 1))
    const pageSize = Math.max(1, Number(query.page_size || 50))
    const filtered = taskLogsFromApi(tasks)
      .filter((item) => !level || item.level === level)
      .filter((item) => !moduleName || item.module === moduleName)
    const start = (page - 1) * pageSize
    return {
      ok: true,
      total: filtered.length,
      items: filtered.slice(start, start + pageSize),
      page,
      page_size: pageSize,
      levels: ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL'],
    }
  } catch {
    return emptyLogResponse(query)
  }
}

export async function fetchLogMetadata() {
  return { ok: true, modules: ['tasks'] }
}

export async function clearLogs() {
  return { ok: true, cleared: 0 }
}

export async function fetchNotifications() {
  return { ok: true, total: 0, items: [] }
}

export async function getUnreadNotificationCount() {
  return { ok: true, unread_count: 0 }
}

export async function markNotificationAsRead(_notificationId?: string) {
  return { ok: true, unread_count: 0 }
}

export async function markAllNotificationsAsRead() {
  return { ok: true, unread_count: 0 }
}

export async function clearNotifications() {
  return { ok: true, unread_count: 0, cleared: 0 }
}

// ----- Stub functions (v2 not implemented yet) -----
// These functions are from Legacy MediaTools and not yet implemented in v2

const v2NotReady = (name: string) => async (..._args: any[]): Promise<any> => {
  throw new Error(name + ': 此功能需要旧版 MediaTools 后端，v2 尚未实现')
}

export function shutdownSystem() { return Promise.resolve({ success: true }) }
export const restartSystem = v2NotReady('restartSystem')
export const getSystemStatus = v2NotReady('getSystemStatus')
export const getModules = v2NotReady('getModules')
export const getWorkspace = v2NotReady('getWorkspace')
export const setWorkspace = v2NotReady('setWorkspace')
export const getTask = v2NotReady('getTask')
export const getTaskList = v2NotReady('getTaskList')

// Legacy MediaTools features not planned for v2
export const runAgent = v2NotReady('runAgent')
export const testAgentConnection = v2NotReady('testAgentConnection')
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
export const fetchPersistedModelConfig = v2NotReady('fetchPersistedModelConfig')
export const savePersistedModelConfig = v2NotReady('savePersistedModelConfig')
export const clearPersistedModelConfig = v2NotReady('clearPersistedModelConfig')
export const cancelJob = v2NotReady('cancelJob')
export const runFetcherDownload = v2NotReady('runFetcherDownload')
