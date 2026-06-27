import { describe, expect, it, vi, afterEach } from 'vitest'

import {
  clearLogs,
  clearNotifications,
  fetchLogMetadata,
  fetchLogs,
  getSystemMetrics,
  getUnreadNotificationCount,
  shutdownSystem,
} from '@/api'

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('v2 API compatibility facade', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('aggregates doctor and task data for the right panel', async () => {
    const fetchMock = vi.fn((path: string) => {
      if (path === '/api/doctor') {
        return Promise.resolve(jsonResponse([
          { name: 'ffmpeg', available: true, path: 'C:/tools/ffmpeg.exe' },
          { name: 'yt-dlp', available: true, path: 'C:/tools/yt-dlp.exe' },
        ]))
      }
      if (path === '/api/fetch/tasks') {
        return Promise.resolve(jsonResponse([
          { id: 'pending-1', title: 'Queued video', source_url: 'https://example.com/a', status: 'pending', progress: 0, stage: 'queued' },
          { id: 'running-1', title: 'Live video', source_url: 'https://example.com/b', status: 'running', progress: 0.42, stage: 'downloading' },
          { id: 'done-1', title: 'Old video', source_url: 'https://example.com/c', status: 'completed', progress: 1, stage: 'completed' },
        ]))
      }
      if (path === '/api/system/metrics') {
        return Promise.resolve(jsonResponse({
          runtime: { uptime_seconds: 3661 },
          system: { cpu_percent: 12.5, memory_percent: 63.2, gpu_percent: 0, gpu_available: false },
          network: {
            upload: { text: '4.0 KB/s' },
            download: { text: '1.5 MB/s' },
            upload_bytes_per_sec: 4096,
            download_bytes_per_sec: 1572864,
          },
        }))
      }
      return Promise.resolve(jsonResponse({ error: 'Not found' }, 404))
    })
    vi.stubGlobal('fetch', fetchMock)

    const metrics = await getSystemMetrics()

    expect(metrics.services).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: 'fetcher', online: true }),
      expect.objectContaining({ id: 'encoder', online: true }),
    ]))
    expect(metrics.tasks).toHaveLength(2)
    expect(metrics.tasks[1]).toEqual(expect.objectContaining({
      id: 'running-1',
      progress: 42,
      can_cancel: true,
    }))
    expect(metrics.task_summary).toEqual(expect.objectContaining({
      active_downloads: 2,
      total_download_records: 3,
      terminal_download_records: 1,
    }))
    expect(metrics.system).toEqual(expect.objectContaining({ cpu_percent: 12.5, memory_percent: 63.2 }))
    expect(metrics.runtime).toEqual(expect.objectContaining({ uptime_seconds: 3661 }))
    expect(metrics.network).toEqual(expect.objectContaining({ upload_bytes_per_sec: 4096, download_bytes_per_sec: 1572864 }))
  })

  it('returns quiet empty metrics when v2 endpoints are temporarily unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(jsonResponse({ error: 'offline' }, 503))))

    const metrics = await getSystemMetrics()

    expect(metrics.tasks).toEqual([])
    expect(metrics.task_summary.active_downloads).toBe(0)
    expect(JSON.stringify(metrics)).not.toContain('旧版 MediaTools 后端')
  })

  it('sends shutdown requests to the v2 backend', async () => {
    const fetchMock = vi.fn(() => Promise.resolve(jsonResponse({ ok: true })))
    vi.stubGlobal('fetch', fetchMock)

    await expect(shutdownSystem()).resolves.toEqual({ ok: true })

    expect(fetchMock).toHaveBeenCalledWith('/api/system/shutdown', expect.objectContaining({
      method: 'POST',
    }))
  })

  it('maps v2 task records into log rows for the log viewer', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(jsonResponse([
      {
        id: 'failed-1',
        title: 'Broken download',
        source_url: 'https://example.com/bad',
        status: 'failed',
        stage: 'failed',
        error: 'network timeout',
        updated_at: 1782450000,
      },
      {
        id: 'done-1',
        title: 'Finished download',
        source_url: 'https://example.com/good',
        status: 'completed',
        stage: 'completed',
        updated_at: 1782450100,
      },
    ]))))

    const logs = await fetchLogs({ level: 'ERROR', page: 1, page_size: 10 })

    expect(logs).toEqual(expect.objectContaining({ ok: true, total: 1, page: 1, page_size: 10 }))
    expect(logs.items[0]).toEqual(expect.objectContaining({
      level: 'ERROR',
      module: 'tasks',
      event: expect.stringContaining('network timeout'),
    }))
    expect(JSON.stringify(logs)).not.toContain('旧版 MediaTools 后端')
  })

  it('returns quiet log and notification fallbacks while v2 backend logging is absent', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(jsonResponse({ error: 'offline' }, 503))))

    await expect(fetchLogs({ page: 2, page_size: 20 })).resolves.toEqual(expect.objectContaining({
      ok: true,
      total: 0,
      items: [],
      page: 2,
      page_size: 20,
    }))
    await expect(fetchLogMetadata()).resolves.toEqual({ ok: true, modules: ['tasks'] })
    await expect(clearLogs()).resolves.toEqual({ ok: true, cleared: 0 })
    await expect(getUnreadNotificationCount()).resolves.toEqual({ ok: true, unread_count: 0 })
    await expect(clearNotifications()).resolves.toEqual({ ok: true, unread_count: 0, cleared: 0 })
  })
})
