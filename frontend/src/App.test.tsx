import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { buildFetchPlan, normalizeUrls } from './api'
import { App } from './App'

function mockFetch(json: unknown) {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(json),
  } as Response)
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('download workbench shell', () => {
  it('renders the legacy-style download workbench', async () => {
    mockFetch([
      { name: 'ffmpeg', available: true, path: '/usr/bin/ffmpeg' },
      { name: 'ffprobe', available: true, path: '/usr/bin/ffprobe' },
      { name: 'yt-dlp', available: true, path: '/usr/bin/yt-dlp' },
    ])

    render(<App />)

    expect(screen.getByRole('heading', { name: '下载工作台' })).toBeInTheDocument()
    expect(screen.getByLabelText('下载参数')).toBeInTheDocument()
    expect(screen.getByLabelText('任务预览')).toBeInTheDocument()
    expect(await screen.findByText('ffmpeg')).toBeInTheDocument()
  })

  it('shows waiting message when doctor is unreachable', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('unreachable'))
    render(<App />)
    expect(await screen.findByText('等待后端 doctor 接入…')).toBeInTheDocument()
  })

  it('normalizes multiline urls', () => {
    expect(normalizeUrls(' https://a.example/video \n\nhttps://b.example/clip ')).toEqual([
      'https://a.example/video',
      'https://b.example/clip',
    ])
  })

  it('does not pass mp4 preset for subtitles-only plans', () => {
    const plan = buildFetchPlan({
      urls: 'https://example.com/video',
      outputDir: 'downloads',
      subtitlesOnly: true,
      subtitleMode: 'both',
      subLangs: 'original',
      convertSubs: 'srt',
      preset: 'mp4',
      nameTemplate: '{title}.{ext}',
      maxConcurrent: 1,
      dryRun: true,
    })

    expect(plan.command).toContain('--subtitles-only')
    expect(plan.command).not.toContain('--preset mp4')
  })
})