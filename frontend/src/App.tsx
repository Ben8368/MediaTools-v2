import { useEffect, useMemo, useState } from 'react'

import { buildFetchPlan, fetchDoctorStatus } from './api'
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

const navItems = ['下载工作台', '媒体工具', '任务记录', '环境状态']

export function App() {
  const [draft, setDraft] = useState<FetchDraft>(initialDraft)
  const [tools, setTools] = useState<DoctorToolState[]>([])
  const plan = useMemo(() => buildFetchPlan(draft), [draft])

  useEffect(() => {
    void fetchDoctorStatus().then(setTools)
  }, [])

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
              <p className="eyebrow">Legacy layout shell</p>
              <h1 id="download-title">下载工作台</h1>
            </div>
            <div className="titlebar-actions">
              <button type="button" title="预览命令" onClick={() => setDraft((value) => ({ ...value, dryRun: true }))}>
                预览
              </button>
              <button type="button" title="提交任务" onClick={() => setDraft((value) => ({ ...value, dryRun: false }))}>
                提交
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
                <strong>{plan.urls.length}</strong>
              </div>
              <div className="task-list">
                {plan.urls.length ? (
                  plan.urls.map((url, index) => (
                    <article className="task-row" key={`${url}-${index}`}>
                      <span className="task-index">{String(index + 1).padStart(2, '0')}</span>
                      <div>
                        <strong>{url}</strong>
                        <p>{draft.subtitlesOnly ? '字幕-only' : draft.preset === 'mp4' ? 'MP4 视频 + 字幕' : '原始格式'}</p>
                      </div>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">等待输入 URL</div>
                )}
              </div>
            </section>
          </div>

          <section className="command-panel" aria-label="命令预览">
            <div className="pane-head">
              <span>v2 契约预览</span>
              <strong>{draft.dryRun ? 'DRY RUN' : 'SUBMIT'}</strong>
            </div>
            <code>{plan.command}</code>
            <p>Summary: {plan.summaryPath}</p>
            {plan.warnings.map((warning) => (
              <p className="warning" key={warning}>
                {warning}
              </p>
            ))}
          </section>
        </section>
      </main>

      <aside className="right-panel" aria-label="系统状态">
        <div className="panel-card">
          <h2>环境状态</h2>
          {tools.map((tool) => (
            <div className="tool-row" key={tool.name}>
              <span className={tool.available ? 'status-dot ok' : 'status-dot'} />
              <div>
                <strong>{tool.name}</strong>
                <p>{tool.path || '等待后端 doctor 接入'}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="panel-card">
          <h2>迁移边界</h2>
          <p>保留 Legacy 的窗口布局、密度和下载工作台路径；媒体处理仍由 Python core / CLI / API 适配层负责。</p>
        </div>
      </aside>
    </div>
  )
}
