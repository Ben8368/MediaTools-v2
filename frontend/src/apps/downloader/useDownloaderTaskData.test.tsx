import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useDownloaderTaskData } from '@/apps/downloader/useDownloaderTaskData'

const apiMocks = vi.hoisted(() => ({
  getActiveTasks: vi.fn(),
  getWeeklyHistory: vi.fn(),
}))

vi.mock('@/api', () => apiMocks)

function TaskProgressProbe() {
  const { queueTasks } = useDownloaderTaskData()
  return <div>{queueTasks[0]?.progress ?? 'loading'}</div>
}

describe('useDownloaderTaskData', () => {
  it('normalizes fractional backend progress for download rows', async () => {
    apiMocks.getWeeklyHistory.mockResolvedValue([])
    apiMocks.getActiveTasks.mockResolvedValue([
      {
        id: 'task-progress',
        title: 'Fractional progress',
        status: 'running',
        progress: 0.05,
        stage: 'downloading',
      },
    ])

    render(<TaskProgressProbe />)

    expect(await screen.findByText('5')).toBeInTheDocument()
  })
})
