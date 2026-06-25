import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { buildFetchPlan, normalizeUrls } from './api'
import { App } from './App'

describe('download workbench shell', () => {
  it('renders the legacy-style download workbench', async () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: '下载工作台' })).toBeInTheDocument()
    expect(screen.getByLabelText('下载参数')).toBeInTheDocument()
    expect(screen.getByLabelText('任务预览')).toBeInTheDocument()
    expect(await screen.findByText('ffmpeg')).toBeInTheDocument()
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
