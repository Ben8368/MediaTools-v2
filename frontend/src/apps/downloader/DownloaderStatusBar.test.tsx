import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DownloaderStatusBar } from '@/apps/downloader/DownloaderStatusBar'

const apiMocks = vi.hoisted(() => ({
  fetchSystemRuntimeMetrics: vi.fn(),
}))

vi.mock('@/api', () => apiMocks)

describe('DownloaderStatusBar', () => {
  it('shows live network speed from system metrics', async () => {
    apiMocks.fetchSystemRuntimeMetrics.mockResolvedValue({
      network: {
        upload: { text: '4.0 KB/s' },
        download: { text: '1.5 MB/s' },
      },
    })

    render(<DownloaderStatusBar detailOpen={false} onToggleDetail={() => {}} />)

    expect(await screen.findByText(/↓ 1.5 MB\/s/)).toBeInTheDocument()
    expect(screen.getByText(/↑ 4.0 KB\/s/)).toBeInTheDocument()
  })
})
