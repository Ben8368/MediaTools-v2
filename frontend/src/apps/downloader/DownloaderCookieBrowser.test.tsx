import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { DownloaderApp } from '@/apps/DownloaderApp'

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

vi.mock('@/api', () => apiMocks)

vi.mock('@/windowStore', () => ({
  useWindowStore: (selector: (state: { openWindow: ReturnType<typeof vi.fn> }) => unknown) =>
    selector({ openWindow: vi.fn() }),
}))

vi.mock('@/apps/FileManagerApp', () => ({
  DirectoryPickerDialog: () => null,
}))

describe('DownloaderApp browser cookie confirmation', () => {
  beforeEach(() => {
    apiMocks.getActiveTasks.mockResolvedValue([])
    apiMocks.getWeeklyHistory.mockResolvedValue([])
    apiMocks.fetchSystemRuntimeMetrics.mockResolvedValue({
      network: {
        upload: { text: '0 B/s' },
        download: { text: '0 B/s' },
      },
    })
    apiMocks.submitFetch.mockResolvedValue({ task_id: 'task-cookie', status: 'pending' })
    vi.spyOn(window, 'confirm').mockReturnValue(false)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requires confirmation before using Chrome cookies', async () => {
    render(<DownloaderApp />)

    fireEvent.click(await screen.findByRole('button', { name: '添加任务' }))
    const cookieSelect = screen.getAllByRole('combobox')[2] as HTMLSelectElement
    fireEvent.change(cookieSelect, { target: { value: 'chrome' } })

    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('不会自动关闭已经打开的浏览器'))
    expect(cookieSelect.value).toBe('none')
  })
})
