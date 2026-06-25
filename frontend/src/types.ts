export type SubtitleMode = 'none' | 'manual' | 'auto' | 'both'

export type FetchDraft = {
  urls: string
  outputDir: string
  subtitlesOnly: boolean
  subtitleMode: SubtitleMode
  subLangs: string
  convertSubs: 'srt' | 'vtt'
  preset: 'mp4' | 'none'
  nameTemplate: string
  maxConcurrent: number
  dryRun: boolean
}

export type DoctorToolState = {
  name: 'ffmpeg' | 'ffprobe' | 'yt-dlp'
  available: boolean
  path?: string
}

export type PlannedFetch = {
  urls: string[]
  command: string
  summaryPath: string
  warnings: string[]
}
