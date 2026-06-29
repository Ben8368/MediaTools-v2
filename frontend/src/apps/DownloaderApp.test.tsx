import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DownloaderApp } from '@/apps/DownloaderApp'
import { computeStats, isTaskCancellable } from '@/apps/downloader/helpers'

const apiMocks = vi.hoisted(() => ({
  cancelTask: vi.fn(),
  clearTaskRecords: vi.fn(),
  deleteTaskRecord: vi.fn(),
  getFetchTaskFileUrl: vi.fn(),
  getActiveTasks: vi.fn(),
  getWeeklyHistory: vi.fn(),
  fetchSystemRuntimeMetrics: vi.fn(),
  submitFetch: vi.fn(),
}))

const openWindowMock = vi.hoisted(() => vi.fn())

vi.mock('@/api', () => apiMocks)

vi.mock('@/windowStore', () => ({
  useWindowStore: (selector: (state: { openWindow: ReturnType<typeof vi.fn> }) => unknown) =>
    selector({ openWindow: openWindowMock }),
}))

vi.mock('@/apps/FileManagerApp', () => ({
  DirectoryPickerDialog: ({ open, onClose, onPick }: {
    open: boolean
    onClose: () => void
    onPick: (path: string) => void
  }) => open ? (
    <div role="dialog" aria-label="选择下载保存目录">
      <button type="button" onClick={() => onPick('/tmp/Media Downloads')}>选择测试目录</button>
      <button type="button" onClick={onClose}>关闭</button>
    </div>
  ) : null,
}))

describe('DownloaderApp helpers', () => {
  it('marks only pending and running tasks as cancellable', () => {
    expect(isTaskCancellable({ status: 'pending' })).toBe(true)
    expect(isTaskCancellable({ status: 'running' })).toBe(true)
    expect(isTaskCancellable({ status: 'completed' })).toBe(false)
    expect(isTaskCancellable({ status: 'failed' })).toBe(false)
    expect(isTaskCancellable({ status: 'cancelled' })).toBe(false)
  })

  it('computes grouped task stats', () => {
    const stats = computeStats([
      { id: '1', type: 'download', name: 'pending', status: 'pending', progress: 0, stage: '', created_at: 1 },
      { id: '2', type: 'download', name: 'running', status: 'running', progress: 30, stage: '', created_at: 2 },
      { id: '3', type: 'download', name: 'done', status: 'completed', progress: 100, stage: '', created_at: 3 },
      { id: '4', type: 'download', name: 'err', status: 'failed', progress: 100, stage: '', created_at: 4 },
      { id: '5', type: 'download', name: 'cancelled', status: 'cancelled', progress: 20, stage: '', created_at: 5 },
    ])

    expect(stats).toMatchObject({
      all: 5,
      downloading: 2,
      completed: 1,
      paused: 1,
      error: 1,
    })
  })
})

describe('DownloaderApp interactions', () => {
  beforeEach(() => {
    apiMocks.getActiveTasks.mockReset()
    apiMocks.getWeeklyHistory.mockReset()
    apiMocks.fetchSystemRuntimeMetrics.mockReset()
    apiMocks.submitFetch.mockReset()
    apiMocks.cancelTask.mockReset()
    apiMocks.clearTaskRecords.mockReset()
    apiMocks.deleteTaskRecord.mockReset()
    apiMocks.getFetchTaskFileUrl.mockReset()
    apiMocks.getFetchTaskFileUrl.mockImplementation((taskId: string, path: string) => `/download/${taskId}?path=${encodeURIComponent(path)}`)
    apiMocks.getWeeklyHistory.mockResolvedValue([])
    apiMocks.fetchSystemRuntimeMetrics.mockResolvedValue({
      network: {
        upload: { text: '4.0 KB/s' },
        download: { text: '1.5 MB/s' },
      },
    })
    apiMocks.submitFetch.mockResolvedValue({ task_id: 'new-task', status: 'pending' })
    apiMocks.cancelTask.mockResolvedValue({ ok: true })
    apiMocks.clearTaskRecords.mockResolvedValue({ ok: true, deleted: 1 })
    apiMocks.deleteTaskRecord.mockResolvedValue({ ok: true, deleted: 1 })
  })

  it('cancels selected running tasks', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([
      {
        id: 'task-1',
        title: 'Example download',
        status: 'running',
        progress: 40,
        stage: 'downloading',
      },
    ])

    render(<DownloaderApp />)

    expect((await screen.findAllByText('Example download')).length).toBeGreaterThan(0)

    fireEvent.click((await screen.findAllByText('Example download'))[0])

    const stopButton = screen.getByLabelText('stop-selected-downloads')
    expect(stopButton).toBeEnabled()

    fireEvent.click(stopButton)

    await waitFor(() => {
      expect(apiMocks.cancelTask).toHaveBeenCalledWith('task-1')
    })
  })

  it('shift-click extends selection across visible rows', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([
        {
          id: 'task-a',
          title: 'Focused task',
          status: 'running',
          progress: 40,
          stage: 'downloading',
        },
        {
          id: 'task-b',
          title: 'Second task',
          status: 'pending',
          progress: 0,
          stage: 'queued',
        },
      ],
    )

    render(<DownloaderApp />)

    const rowA = (await screen.findAllByText('Focused task'))[0].closest('div.dl-row') as HTMLElement
    const rowB = (await screen.findAllByText('Second task'))[0].closest('div.dl-row') as HTMLElement
    fireEvent.click(rowA)
    expect(screen.getByLabelText('stop-selected-downloads')).toBeEnabled()

    fireEvent.click(rowB, { shiftKey: true })
    expect(screen.getByLabelText('select-all-downloads')).toHaveTextContent('取消')
  })

  it('keeps stop disabled for completed history tasks', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([
        {
          id: 'task-2',
          title: 'Finished download',
          status: 'completed',
          progress: 100,
          stage: 'done',
        },
      ],
    )

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: /已完成/ }))
    expect((await screen.findAllByText('Finished download')).length).toBeGreaterThan(0)

    fireEvent.click((await screen.findAllByText('Finished download'))[0])
    expect(screen.getByLabelText('stop-selected-downloads')).toBeDisabled()
  })

  it('shows queue and weekly history together on the default all view', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([
        {
          id: 'task-history',
          title: 'Old completed download',
          status: 'completed',
          progress: 100,
          stage: 'done',
        },
      ],
    )

    render(<DownloaderApp />)

    await waitFor(() => {
      expect(apiMocks.getWeeklyHistory).toHaveBeenCalled()
    })
    expect(await screen.findByText('Old completed download')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /已完成/ }))
    expect(await screen.findByText('Old completed download')).toBeInTheDocument()
  })

  it('renders readable toolbar, empty state, and add-form labels', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])

    render(<DownloaderApp />)

    expect(await screen.findByText('暂无任务')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('搜索标题或链接')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '添加任务' })).toBeInTheDocument()
    expect(screen.getByText('停止')).toBeInTheDocument()
    expect(screen.getByText('重试')).toBeInTheDocument()
    expect(screen.getByText('删除')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '添加任务' }))

    expect(screen.getByText('下载链接')).toBeInTheDocument()
    expect(screen.getByText('平台')).toBeInTheDocument()
    expect(screen.getByText('字幕')).toBeInTheDocument()
    expect(screen.getByText('目标目录')).toBeInTheDocument()
    expect(screen.getByText('登录态')).toBeInTheDocument()
    expect(screen.getByText('智能识别')).toBeInTheDocument()
    expect(screen.getByText('留空则使用默认下载目录')).toBeInTheDocument()
    expect(screen.getByText('不使用浏览器登录态')).toBeInTheDocument()
  })

  it('keeps short-video dropdown labels readable and disables subtitles', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    fireEvent.change(screen.getAllByRole('combobox')[0], {
      target: { value: 'short_video' },
    })

    expect(screen.getByText('短视频平台')).toBeInTheDocument()
    expect(screen.getByText('当前平台不提供字幕')).toBeInTheDocument()
    expect(screen.getByText('已自动切换为仅视频，适合大多数短视频平台。')).toBeInTheDocument()
  })

  it('shows a newly submitted task immediately in the queue', async () => {
    let activeTaskCalls = 0
    apiMocks.getActiveTasks.mockImplementation(() => {
      activeTaskCalls += 1
      return activeTaskCalls === 1 ? Promise.resolve([]) : new Promise(() => {})
    })
    apiMocks.submitFetch.mockResolvedValue({ task_id: 'task-new', status: 'pending' })

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    fireEvent.change(document.querySelector('.dl-add-form textarea') as HTMLTextAreaElement, {
      target: { value: 'https://example.com/video' },
    })

    fireEvent.click(screen.getByRole('button', { name: '确认添加' }))

    await waitFor(() => {
      expect(apiMocks.submitFetch).toHaveBeenCalledWith(
        expect.objectContaining({
          urls: ['https://example.com/video'],
          preset: 'mp4',
        }),
      )
    })
    expect(screen.queryByRole('button', { name: '确认添加' })).not.toBeInTheDocument()
    expect(await screen.findByText('https://example.com/video')).toBeInTheDocument()
  })

  it('uses the selected directory when submitting a new task', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.submitFetch.mockResolvedValue({
      task_id: 'task-dir',
      status: 'pending',
    })

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    fireEvent.click(screen.getByText('选择目录'))
    fireEvent.click(screen.getByRole('button', { name: '选择测试目录' }))
    fireEvent.change(document.querySelector('.dl-add-form textarea') as HTMLTextAreaElement, {
      target: { value: 'https://example.com/video' },
    })
    fireEvent.click(screen.getByRole('button', { name: '确认添加' }))

    await waitFor(() => {
      expect(apiMocks.submitFetch).toHaveBeenCalledWith(
        expect.objectContaining({
          output_dir: '/tmp/Media Downloads',
        }),
      )
    })
  })

  it('passes selected browser cookies for authenticated downloads', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.submitFetch.mockResolvedValue({
      task_id: 'task-cookie',
      status: 'pending',
    })

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    fireEvent.change(screen.getAllByRole('combobox')[2], {
      target: { value: 'chrome' },
    })
    fireEvent.change(document.querySelector('.dl-add-form textarea') as HTMLTextAreaElement, {
      target: { value: 'https://youtu.be/-28MFc9TMw0?si=n22fyl0em7b0uGbi' },
    })
    fireEvent.click(screen.getByRole('button', { name: '确认添加' }))

    await waitFor(() => {
      expect(apiMocks.submitFetch).toHaveBeenCalledWith(
        expect.objectContaining({
          cookies_from_browser: 'chrome',
        }),
      )
    })
  })

  it('turns subtitles off automatically for short video mode submissions', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.submitFetch.mockResolvedValue({
      task_id: 'task-short',
      status: 'pending',
    })

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    fireEvent.change(screen.getAllByRole('combobox')[0], {
      target: { value: 'short_video' },
    })
    fireEvent.change(document.querySelector('.dl-add-form textarea') as HTMLTextAreaElement, {
      target: { value: 'https://example.com/short' },
    })
    fireEvent.click(screen.getByRole('button', { name: '确认添加' }))

    await waitFor(() => {
      expect(apiMocks.submitFetch).toHaveBeenCalledWith(
        expect.objectContaining({
          urls: ['https://example.com/short'],
          write_subs: false,
          write_auto_subs: false,
        }),
      )
    })
  })

  it('selects visible tasks from the current filtered list', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([
        {
          id: 'task-3',
          title: 'Broken download',
          status: 'failed',
          progress: 12,
          stage: 'failed',
        },
      ],
    )

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: /错误/ }))
    await screen.findByText('Broken download')
    fireEvent.click(screen.getByLabelText('select-all-downloads'))
    expect(screen.getByLabelText('select-all-downloads')).toHaveTextContent('取消')
  })

  it('clears selected finished records', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([
        {
          id: 'task-5',
          title: 'Done A',
          status: 'completed',
          progress: 100,
          stage: 'done',
        },
        {
          id: 'task-6',
          title: 'Done B',
          status: 'failed',
          progress: 10,
          stage: 'failed',
        },
      ],
    )

    render(<DownloaderApp />)

    await screen.findByText('Done B')
    await screen.findByText('Done A')
    fireEvent.click(screen.getByLabelText('select-all-downloads'))
    fireEvent.click(screen.getByLabelText('delete-download-records'))

    await waitFor(() => {
      expect(apiMocks.clearTaskRecords).toHaveBeenCalledWith(['task-5', 'task-6'])
    })
  })

  it('deletes a single selected finished record', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([
        {
          id: 'task-7',
          title: 'Done selected',
          status: 'completed',
          progress: 100,
          stage: 'done',
        },
      ],
    )

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: /已完成/ }))
    await screen.findByText('Done selected')
    fireEvent.click(screen.getByLabelText('select-all-downloads'))
    fireEvent.click(screen.getByLabelText('delete-download-records'))

    await waitFor(() => {
      expect(apiMocks.deleteTaskRecord).toHaveBeenCalledWith('task-7')
    })
  })

  it('downloads a completed task output from the row menu', async () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([
        {
          id: 'task-file',
          title: 'File ready',
          status: 'completed',
          progress: 100,
          stage: 'completed',
          output_files: ['/tmp/video.mp4'],
        },
      ],
    )

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: /已完成/ }))
    await screen.findByText('File ready')
    fireEvent.click(screen.getByLabelText('更多操作'))
    fireEvent.click(await screen.findByRole('menuitem', { name: '下载文件' }))

    expect(apiMocks.getFetchTaskFileUrl).toHaveBeenCalledWith('task-file', '/tmp/video.mp4')
    expect(openSpy).toHaveBeenCalledWith('/download/task-file?path=%2Ftmp%2Fvideo.mp4', '_blank', 'noopener')
    openSpy.mockRestore()
  })

  it('renders task details for the focused row', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([
        {
          id: 'task-4',
          title: 'Test Clip',
          source_url: 'https://www.youtube.com/watch?v=test',
          status: 'running',
          progress: 15,
          stage: 'downloading',
          output_files: ['D:/Downloads/test.mp4'],
        },
      ],
    )

    render(<DownloaderApp />)

    fireEvent.click((await screen.findAllByText('Test Clip'))[0])

    expect(screen.queryByText('下载请求快照')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '任务详情' }))

    expect(screen.getAllByText('Test Clip').length).toBeGreaterThanOrEqual(1)
  })

  it('keeps the detail drawer usable while the add form is open', async () => {
    apiMocks.getActiveTasks.mockResolvedValue([
        {
          id: 'task-8',
          title: 'Overlay task',
          status: 'running',
          progress: 15,
          stage: 'downloading',
          params: {
            url: 'https://example.com/overlay',
          },
        },
      ],
    )

    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    fireEvent.click((await screen.findAllByText('Overlay task'))[0].closest('div.dl-row') as HTMLElement)

    fireEvent.click(screen.getByRole('button', { name: '任务详情' }))

    expect(screen.getByText('下载请求快照')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '确认添加' })).toBeInTheDocument()
  })
})
