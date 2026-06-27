import { PLATFORM_OPTIONS } from '@/apps/downloader/constants'
import type { CookieBrowser, DownloadPlatform, PlatformOption } from '@/apps/downloader/types'

type DownloaderAddFormProps = {
  taskUrl: string
  taskPlatform: DownloadPlatform
  taskSubtitles: boolean
  taskOutputDir: string
  taskCookieBrowser: CookieBrowser
  selectedPlatform: PlatformOption
  addingTask: boolean
  submitError: string
  onTaskUrlChange: (value: string) => void
  onTaskPlatformChange: (value: DownloadPlatform) => void
  onTaskSubtitlesChange: (value: boolean) => void
  onTaskOutputDirChange: (value: string) => void
  onTaskCookieBrowserChange: (value: CookieBrowser) => void
  onOpenDirectoryPicker: () => void
  onSubmit: () => void
  onClose: () => void
}

export function DownloaderAddForm({
  taskUrl,
  taskPlatform,
  taskSubtitles,
  taskOutputDir,
  taskCookieBrowser,
  selectedPlatform,
  addingTask,
  submitError,
  onTaskUrlChange,
  onTaskPlatformChange,
  onTaskSubtitlesChange,
  onTaskOutputDirChange,
  onTaskCookieBrowserChange,
  onOpenDirectoryPicker,
  onSubmit,
  onClose,
}: DownloaderAddFormProps) {
  return (
    <div className="dl-add-form">
      <div className="dl-field">
        <label>下载链接</label>
        <textarea
          value={taskUrl}
          onChange={(event) => onTaskUrlChange(event.target.value)}
          placeholder={'输入视频 URL（YouTube、Bilibili 等）\n支持多行，每行一个链接'}
          rows={4}
          style={{ resize: 'vertical', minHeight: '80px' }}
        />
      </div>

      <div className="dl-form-row">
        <div className="dl-field">
          <label>平台</label>
          <select value={taskPlatform} onChange={(event) => onTaskPlatformChange(event.target.value as DownloadPlatform)}>
            {PLATFORM_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <small className="dl-field-hint">{selectedPlatform.hint}</small>
        </div>
        <div className="dl-field">
          <label>字幕</label>
          <select
            value={String(selectedPlatform.supportsSubtitles ? taskSubtitles : false)}
            disabled={!selectedPlatform.supportsSubtitles}
            onChange={(event) => onTaskSubtitlesChange(event.target.value === 'true')}
          >
            {selectedPlatform.supportsSubtitles ? (
              <>
                <option value="true">下载字幕</option>
                <option value="false">仅视频</option>
              </>
            ) : (
              <option value="false">当前平台不提供字幕</option>
            )}
          </select>
          {!selectedPlatform.supportsSubtitles && (
            <small className="dl-field-hint">已自动切换为仅视频，适合大多数短视频平台。</small>
          )}
        </div>
      </div>

      <div className="dl-form-row">
        <div className="dl-field dl-field--path">
          <label>目标目录</label>
          <div className="dl-path-field">
            <button
              type="button"
              className={`dl-path-display ${taskOutputDir ? 'dl-path-display--filled' : ''}`}
              onClick={onOpenDirectoryPicker}
            >
              <span className="dl-path-display__label">{taskOutputDir || '留空则使用默认下载目录'}</span>
              <span className="dl-path-display__action">{taskOutputDir ? '更改' : '选择目录'}</span>
            </button>
            {taskOutputDir && (
              <button type="button" className="dl-btn dl-btn--ghost" onClick={() => onTaskOutputDirChange('')}>
                清空
              </button>
            )}
          </div>
        </div>
        <div className="dl-field">
          <label>登录态</label>
          <select
            value={taskCookieBrowser}
            onChange={(event) => onTaskCookieBrowserChange(event.target.value as CookieBrowser)}
          >
            <option value="none">不使用浏览器登录态</option>
            <option value="chrome">Chrome</option>
            <option value="safari">Safari</option>
            <option value="firefox">Firefox</option>
          </select>
          <small className="dl-field-hint">遇到 YouTube 登录或机器人验证时，选择已登录的浏览器。</small>
        </div>
      </div>

      <div className="dl-form-actions">
        <button className="dl-btn dl-btn--primary" onClick={onSubmit} disabled={addingTask || !taskUrl.trim()}>
          {addingTask ? '提交中...' : '确认添加'}
        </button>
        <button className="dl-btn" onClick={onClose}>
          取消
        </button>
      </div>
      {submitError && <div className="dl-form-error">{submitError}</div>}
    </div>
  )
}
