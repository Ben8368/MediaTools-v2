import { useCallback, useEffect, useMemo, useState } from 'react'

import { AppLayout } from '@/AppLayout'
import {
  fetchAssets,
  getModules,
  getSystemStatus,
  getWorkspace,
  runEncoder,
  setWorkspace,
} from '@/api'
import { PlusIcon } from '@/apps/downloader/icons'
import {
  Field,
  PathInput,
  PrimaryButton,
  ResultBox,
  ToolbarButton,
} from '@/apps/mediatools/primitives'
import type { AnyRecord } from '@/types'

export function DashboardApp() {
  const [status, setStatus] = useState<AnyRecord | null>(null)
  const [modules, setModules] = useState<AnyRecord[]>([])
  const [workspace, setWorkspaceState] = useState<AnyRecord | null>(null)

  async function refresh() {
    const [statusData, moduleData, workspaceData] = await Promise.all([getSystemStatus(), getModules(), getWorkspace()])
    setStatus(statusData)
    setModules(moduleData.modules || moduleData.items || [])
    setWorkspaceState(workspaceData)
  }

  useEffect(() => { void refresh() }, [])

  return (
    <AppLayout>
      <div className="tool-app">
        <section className="tool-hero">
          <div>
            <div className="tool-eyebrow">MediaTools Console</div>
            <h2>控制台</h2>
            <p>集中查看后端、模块和当前工作区状态，确认自动化链路是否可用。</p>
          </div>
          <div className={`tool-ready ${status?.ok === false ? 'tool-ready--warn' : 'tool-ready--online'}`}>
            <span>{status?.ok === false ? '异常' : '在线'}</span>
            <small>{workspace?.project_root || '默认工作区'}</small>
          </div>
        </section>
        <div className="tool-metrics">
          <div className="tool-metric"><span>后端状态</span><strong>{status?.ok === false ? '异常' : '在线'}</strong></div>
          <div className="tool-metric"><span>模块数量</span><strong>{modules.length || 0}</strong></div>
          <div className="tool-metric"><span>工作区</span><strong>{workspace?.project_root ? '已设置' : '默认'}</strong></div>
          <div className="tool-metric"><span>任务中心</span><strong>已连接</strong></div>
        </div>
        <section className="tool-panel">
          <div className="tool-section-head">
            <div>
              <h3>模块状态</h3>
              <p>按服务能力列出当前可用模块。</p>
            </div>
            <ToolbarButton onClick={() => void refresh()}>刷新</ToolbarButton>
          </div>
          <div className="tool-module-grid">
            {modules.map((item) => (
              <div className="tool-module" key={item.id || item.name}>
                <div><strong>{item.name || item.id}</strong><span>{item.desc || '-'}</span></div>
                <em>{item.status || (item.dep_ok ? 'online' : 'offline')}</em>
              </div>
            ))}
          </div>
        </section>
        <section className="tool-panel">
          <div className="tool-section-head"><h3>工作区详情</h3></div>
          <ResultBox value={workspace || '正在读取工作区'} />
        </section>
      </div>
    </AppLayout>
  )
}

export function EncoderApp() {
  const [inputPath, setInputPath] = useState('')
  const [outputPath, setOutputPath] = useState('')
  const [codec, setCodec] = useState('H.264 (AVC)')
  const [crf, setCrf] = useState(23)
  const [preset, setPreset] = useState('medium')
  const [result, setResult] = useState<unknown>('等待转码')

  async function submit() {
    setResult('正在提交转码任务...')
    try {
      setResult(await runEncoder({ input_path: inputPath, output_path: outputPath || undefined, codec, crf, preset }))
    } catch (err: any) {
      setResult(err?.message || '转码失败')
    }
  }

  return (
    <AppLayout>
      <div className="tool-app">
        <section className="tool-hero">
          <div>
            <div className="tool-eyebrow">Video Encoder</div>
            <h2>视频转码</h2>
            <p>为剪辑、上传和归档生成稳定的 H.264/H.265 输出，并进入任务中心跟踪进度。</p>
          </div>
          <div className="tool-ready"><span>{codec.includes('265') ? 'HEVC' : 'AVC'}</span><small>CRF {crf} / {preset}</small></div>
        </section>
        <div className="tool-workspace">
          <section className="tool-panel">
            <div className="tool-section-head"><div><h3>转码参数</h3><p>输出路径留空时由后端生成默认文件。</p></div></div>
            <Field label="输入文件"><PathInput value={inputPath} onChange={setInputPath} mode="file" /></Field>
            <Field label="输出文件"><PathInput value={outputPath} onChange={setOutputPath} mode="any" /></Field>
            <div className="tool-form-grid">
              <Field label="编码"><select value={codec} onChange={(event) => setCodec(event.target.value)}><option>H.264 (AVC)</option><option>H.265 (HEVC)</option><option value="Audio Only">Audio Only</option></select></Field>
              <Field label="CRF"><input type="number" min={0} max={51} value={crf} onChange={(event) => setCrf(Number(event.target.value))} /></Field>
              <Field label="预设"><select value={preset} onChange={(event) => setPreset(event.target.value)}><option>slow</option><option>medium</option><option>fast</option><option>veryfast</option></select></Field>
            </div>
            <PrimaryButton onClick={submit} disabled={!inputPath}>开始转码</PrimaryButton>
          </section>
          <section className="tool-panel">
            <div className="tool-section-head"><h3>任务回执</h3></div>
            <ResultBox value={result} />
          </section>
        </div>
      </div>
    </AppLayout>
  )
}

export function AssetsApp() {
  const [directory, setDirectory] = useState('')
  const [keyword, setKeyword] = useState('')
  const [assetType, setAssetType] = useState('')
  const [result, setResult] = useState<AnyRecord>({ items: [] })
  const items: AnyRecord[] = result.items || []

  async function scan() {
    try {
      setResult(await fetchAssets({ directory, keyword, asset_type: assetType }))
    } catch (err: any) {
      setResult({ items: [], error: err?.message || '扫描失败' })
    }
  }

  useEffect(() => { void scan() }, [])

  return (
    <AppLayout>
      <div className="tool-app">
        <section className="tool-hero">
          <div>
            <div className="tool-eyebrow">Asset Library</div>
            <h2>素材库</h2>
            <p>扫描工作区或指定目录，按类型和关键词筛选视频、音频、图片和字幕素材。</p>
          </div>
          <div className="tool-ready"><span>{items.length}</span><small>当前结果</small></div>
        </section>
        <section className="tool-panel">
          <div className="tool-section-head">
            <div><h3>扫描筛选</h3><p>留空目录时使用当前工作区。</p></div>
          </div>
          <div className="tool-filter-grid">
            <Field label="扫描目录"><PathInput value={directory} onChange={setDirectory} mode="directory" placeholder="留空则使用当前工作区" /></Field>
            <Field label="关键词"><input value={keyword} onChange={(event) => setKeyword(event.target.value)} /></Field>
            <Field label="类型"><select value={assetType} onChange={(event) => setAssetType(event.target.value)}><option value="">全部</option><option value="video">视频</option><option value="audio">音频</option><option value="image">图片</option><option value="subtitle">字幕</option></select></Field>
          </div>
          <PrimaryButton onClick={scan}>扫描素材</PrimaryButton>
        </section>
        <section className="tool-panel">
          <div className="tool-section-head"><div><h3>扫描结果</h3><p>{result.error || `显示前 ${Math.min(items.length, 80)} 项`}</p></div></div>
          <div className="tool-asset-list">
            {items.slice(0, 80).map((item: AnyRecord) => (
              <div className="tool-asset-row" key={item.path || item.name}>
                <strong>{item.name}</strong><span>{item.type || '-'} · {item.size_mb ?? item.size ?? 0} {item.size_mb !== undefined ? 'MB' : 'bytes'}</span><em>{item.directory || item.path}</em>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppLayout>
  )
}

export function WorkspaceApp() {
  const [projectRoot, setProjectRoot] = useState('')
  const [result, setResult] = useState<unknown>('正在读取工作区')

  async function refresh() {
    const data = await getWorkspace()
    setProjectRoot(data.project_root || '')
    setResult(data)
  }

  async function save() {
    setResult(await setWorkspace(projectRoot))
  }

  useEffect(() => { void refresh() }, [])

  return (
    <AppLayout>
      <div className="tool-app">
        <section className="tool-hero">
          <div>
            <div className="tool-eyebrow">Workspace</div>
            <h2>工作区设置</h2>
            <p>切换 MediaTools 项目根目录，下载、分析、导出和日志都会按工作区隔离。</p>
          </div>
          <div className="tool-ready"><span>Workspace</span><small>{projectRoot || '默认工作区'}</small></div>
        </section>
        <div className="tool-workspace">
          <section className="tool-panel">
            <div className="tool-section-head"><div><h3>项目根目录</h3><p>建议选择专门的 MediaTools 项目目录。</p></div></div>
            <Field label="项目根目录"><PathInput value={projectRoot} onChange={setProjectRoot} mode="directory" /></Field>
            <div className="tool-actions">
              <PrimaryButton onClick={save} disabled={!projectRoot}>切换工作区</PrimaryButton>
              <ToolbarButton onClick={() => void refresh()}>刷新</ToolbarButton>
            </div>
          </section>
          <section className="tool-panel">
            <div className="tool-section-head"><h3>当前配置</h3></div>
            <ResultBox value={result} />
          </section>
        </div>
      </div>
    </AppLayout>
  )
}

export { PhotoshopApp } from './PhotoshopApp'

export { FileManagerApp } from './FileManagerApp'

export { AgentApp } from './AIAssistantApp'
