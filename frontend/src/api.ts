import type { DoctorToolState, FetchDraft, PlannedFetch } from './types'

const quote = (value: string) => `"${value.replace(/"/g, '\\"')}"`

export function normalizeUrls(input: string): string[] {
  return input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
}

export function buildFetchPlan(draft: FetchDraft): PlannedFetch {
  const urls = normalizeUrls(draft.urls)
  const outputDir = draft.outputDir.trim() || 'downloads'
  const summaryPath = `${outputDir.replace(/[\\/]+$/, '')}/summary.json`
  const args = ['python', '-m', 'mediatools', 'fetch']

  if (urls.length === 1) {
    args.push(quote(urls[0]), quote(outputDir))
  } else {
    args.push(quote(outputDir), '--input-file', quote('urls.txt'))
  }

  if (draft.dryRun) args.push('--dry-run')
  if (draft.subtitlesOnly) args.push('--subtitles-only')
  if (draft.subtitleMode === 'manual') args.push('--write-subs')
  if (draft.subtitleMode === 'auto') args.push('--write-auto-subs')
  if (draft.subtitleMode === 'both') args.push('--write-subs', '--write-auto-subs')
  if (draft.subLangs.trim()) args.push('--sub-langs', quote(draft.subLangs.trim()))
  if (draft.convertSubs) args.push('--convert-subs', draft.convertSubs)
  if (draft.preset !== 'none' && !draft.subtitlesOnly) args.push('--preset', draft.preset)
  if (draft.nameTemplate.trim()) args.push('--name-template', quote(draft.nameTemplate.trim()))
  args.push('--max-concurrent', String(draft.maxConcurrent))
  args.push('--summary-json', quote(summaryPath))

  const warnings: string[] = []
  if (urls.length === 0) warnings.push('请先输入至少一个 URL。')
  if (urls.length > 1) warnings.push('批量 URL 会在接入后端时写入临时 input-file；前端不会直接处理媒体下载。')
  if (draft.subtitlesOnly && draft.preset !== 'none') warnings.push('字幕-only 模式不会传递视频格式预设。')

  return {
    urls,
    command: args.join(' '),
    summaryPath,
    warnings,
  }
}

export async function fetchDoctorStatus(): Promise<DoctorToolState[]> {
  try {
    const response = await fetch('/api/doctor')
    if (!response.ok) throw new Error(response.statusText)
    return (await response.json()) as DoctorToolState[]
  } catch {
    return [
      { name: 'ffmpeg', available: false },
      { name: 'ffprobe', available: false },
      { name: 'yt-dlp', available: false },
    ]
  }
}
