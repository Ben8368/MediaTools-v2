import { useCallback, useEffect, useRef, useState } from 'react'

import { buildFetchPlan, fetchDoctorStatus, fetchPlan as apiFetchPlan, pollTasks, submitFetch } from './api'
import type { DoctorToolState, FetchDraft } from './types'

const initialDraft: FetchDraft = {
  urls: '',
  outputDir: 'downloads',
  subtitlesOnly: false,
  subtitleMode: 'both',
  subLangs: 'original',
  convertSubs: 'srt',
  preset: 'mp4',
  nameTemplate: '{lang}-{author}-{title}-{platform}.{ext}',
  maxConcurrent: 1,
  dryRun: true,
}

type TaskRecord = {
  id: string
  title: string
  source_url: string
  status: string
  progress: number
  stage: string
  output_files: string[]
  error?: string | null
}

const navItems = ['下载工作台', '媒体工具', '任务记录', '环境状态']

export function App() {
  const [draft, setDraft] = useState<FetchDraft>(initialDraft)
  const [tools, setTools] = useState<DoctorToolState[]>([])
  const [tasks, setTasks] = useState<TaskRecord[]>([])
  const [planResult, setPlanResult] = useState<{ items: { url: string; command: string; status: string; error?: string }[]; command: string; warnings: string[] } | null>(null)
  const [planLoading, setPlanLoading] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [planError, setPlanError] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval>>()

  const localPlan = buildFetchPlan(draft)

  useEffect(() => {
    fetchDoctorStatus().then(setTools).catch(() => setTools([]))
  }, [])

  useEffect(() => {
    pollingRef.current = setInterval(() => {
      void pollTasks().then(setTasks)
    }, 2000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [])

  const activeCount = tasks.filter((t) => t.status === 'running' || t.status === 'queued').length

  const handlePreview = useCallback(async () => {
    setPlanLoading(true)
    setPlanError(null)
    setPlanResult(null)
    try {
      const result = await apiFetchPlan(draft)
      setPlanResult(result)
    } catch (err) {
      setPlanError(err instanceof Error ? err.message : '请求失败')
    } finally {
      setPlanLoading(false)
    }
  }, [draft])

  const handleSubmit = useCallback(async () => {
    setSubmitLoading(true)
    try {
      await submitFetch(draft)
    } catch (err) {
      alert(err instanceof Error ? err.message : '提交失败')
    } finally {
      setSubmitLoading(false)
    }
  }, [draft])

  const displayPlan = planResult || { items: localPlan.urls.map((u) => ({ url: u, command: localPlan.command, status: 'planned' })), command: localPlan.command, warnings: localPlan.warnings }

  return (
    <div className="desktop-shell">
      <aside className="left-nav" aria-label="主导航">
        <div className="brand-mark">
          <span>MT</span>
        </div>
        <nav>
          {navItems.map((item, index) => (
            <button key={item} className={index === 0 ? 'nav-button nav-button-active' : 'nav-button'} type="button">
              <span className="nav-dot" />
              {item}
            </button>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <section className="window-panel" aria-labelledby="download-title">
          <header className="window-titlebar">
            <div>
              <p className="eyebrow">v2 API 已接线</p>
              <h1 id="download-title">下载工作台</h1>
            </div>
            <div className="titlebar-actions">
              <button type="button" title="预览命令" onClick={handlePreview} disabled={planLoading}>
                {planLoading ? '...' : '预览'}
              </button>
              <button type="button" title="提交任务" onClick={handleSubmit} disabled={submitLoading}>
                {submitLoading ? '...' : '提交'}
              </button>
            </div>
          </header>

          <div className="download-grid">
            <section className="form-pane" aria-label="下载参数">
              <label className="field field-full">
                <span>URL 列表</span>
                <textarea
                  value={draft.urls}
                  placeholder="一行一个 http/https 链接"
                  onChange={(event) => setDraft({ ...draft, urls: event.target.value })}
                />
              </label>

              <label className="field">
                <span>输出目录</span>
                <input value={draft.outputDir} onChange={(event) => setDraft({ ...draft, outputDir: event.target.value })} />
              </label>

              <label className="field">
                <span>字幕语言</span>
                <input value={draft.subLangs} onChange={(event) => setDraft({ ...draft, subLangs: event.target.value })} />
              </label>

              <label className="field">
                <span>字幕来源</span>
                <select
                  value={draft.subtitleMode}
                  onChange={(event) => setDraft({ ...draft, subtitleMode: event.target.value as FetchDraft['subtitleMode'] })}
                >
                  <option value="none">不下载字幕</option>
                  <option value="manual">人工字幕</option>
                  <option value="auto">自动字幕</option>
                  <option value="both">人工 + 自动</option>
                </select>
              </label>

              <label className="field">
                <span>格式预设</span>
                <select value={draft.preset} onChange={(event) => setDraft({ ...draft, preset: event.target.value as FetchDraft['preset'] })}>
                  <option value="mp4">H264/AAC MP4</option>
                  <option value="none">不指定</option>
                </select>
              </label>

              <label className="field">
                <span>并发</span>
                <input
                  min={1}
                  max={16}
                  type="number"
                  value={draft.maxConcurrent}
                  onChange={(event) => setDraft({ ...draft, maxConcurrent: Number(event.target.value || 1) })}
                />
              </label>

              <label className="field check-row">
                <input
                  type="checkbox"
                  checked={draft.subtitlesOnly}
                  onChange={(event) => setDraft({ ...draft, subtitlesOnly: event.target.checked })}
                />
                <span>只下载字幕</span>
              </label>

              <label className="field check-row">
                <input type="checkbox" checked={draft.dryRun} onChange={(event) => setDraft({ ...draft, dryRun: event.target.checked })} />
                <span>dry-run 预览</span>
              </label>

              <label className="field field-full">
                <span>命名模板</span>
                <input value={draft.nameTemplate} onChange={(event) => setDraft({ ...draft, nameTemplate: event.target.value })} />
              </label>
            </section>

            <section className="task-pane" aria-label="任务预览">
              <div className="pane-head">
                <span>任务队列</span>
                <strong>{tasks.length} (进行中 {activeCount})</strong>
              </div>
              <div className="task-list">
                {tasks.length > 0 ? (
                  tasks.map((task) => (
                    <article className="task-row" key={task.id}>
                      <span className="task-index">{task.id.slice(-6)}</span>
                      <div>
                        <strong>{task.title}</strong>
                        <p className={task.status === 'failed' ? 'warning' : undefined}>
                          {task.stage} — {task.status}
                          {task.error && ` — ${task.error}`}
                        </p>
                      </div>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">
                    {planResult ? '暂无任务，点击"提交"开始下载' : '等待输入 URL'}
                  </div>
                )}
              </div>
            </section>
          </div>

          <section className="command-panel" aria-label="命令预览">
            <div className="pane-head">
              <span>v2 契约预览</span>
              <strong>{planResult ? 'SERVER' : 'LOCAL'}</strong>
            </div>
            <code>{displayPlan.command}</code>
            {planError && <p className="warning">{planError}</p>}
            {displayPlan.warnings.map((warning) => (
              <p className="warning" key={warning}>
                {warning}
              </p>
            ))}
            {displayPlan.items.slice(0, 5).map((item) => (
              <div key={item.url} style={{ fontSize: '0.75rem', marginBottom: 4, opacity: 0.7 }}>
                [{item.status}] {item.url}
              </div>
            ))}
          </section>
        </section>
      </main>

      <aside className="right-panel" aria-label="系统状态">
        <div className="panel-card">
          <h2>环境状态</h2>
          {tools.length > 0 ? (
            tools.map((tool) => (
              <div className="tool-row" key={tool.name}>
                <span className={tool.available ? 'status-dot ok' : 'status-dot'} />
                <div>
                  <strong>{tool.name}</strong>
                  <p>{tool.available ? (tool.path || '可用') : '未找到'}</p>
                </div>
              </div>
            ))
          ) : (
            <p>等待后端 doctor 接入…</p>
          )}
        </div>
        <div className="panel-card">
          <h2>迁移边界</h2>
          <p>保留 Legacy 的窗口布局、密度和下载工作台路径；媒体处理仍由 Python API 适配层负责。</p>
        </div>
      </aside>
    </div>
  )
}