import type { ComponentType } from 'react'

import {
  AgentApp,
  AssetsApp,
  DashboardApp,
  EncoderApp,
  PhotoshopApp,
  WorkspaceApp,
  FileManagerApp,
} from '@/apps/MediaToolsApps'
import { DownloaderApp } from '@/apps/DownloaderApp'
import { SettingsApp } from '@/apps/SettingsApp'
import { LogViewer } from '@/LogViewer'
import { APP_ICON_PATHS } from '@/icon-library'

export type RegisteredApp = {
  id: string
  title: string
  label: string
  icon: string
  component: ComponentType
  launcherVisible?: boolean
}

export const appRegistry: RegisteredApp[] = [
  { id: 'dashboard', label: '控制台', title: '控制台', icon: APP_ICON_PATHS.dashboard, component: DashboardApp, launcherVisible: false },
  { id: 'fetcher', label: '下载', title: '下载', icon: APP_ICON_PATHS.fetcher, component: DownloaderApp },
  { id: 'agent', label: 'AI助手', title: 'AI助手', icon: APP_ICON_PATHS.agent, component: AgentApp },
  { id: 'ps', label: 'PS', title: 'Photoshop 自动化', icon: APP_ICON_PATHS.photoshop, component: PhotoshopApp },
  { id: 'photoshop', label: 'Photoshop', title: 'Photoshop 自动化', icon: APP_ICON_PATHS.photoshop, component: PhotoshopApp, launcherVisible: false },
  { id: 'filebrowser', label: '文件管理', title: '文件管理', icon: APP_ICON_PATHS.filebrowser, component: FileManagerApp },
  { id: 'assets', label: '素材库', title: '素材库', icon: APP_ICON_PATHS.assets, component: AssetsApp, launcherVisible: false },
  { id: 'encoder', label: '转码', title: '视频转码', icon: APP_ICON_PATHS.encoder, component: EncoderApp, launcherVisible: false },
  { id: 'workspace', label: '工作区', title: '工作区', icon: APP_ICON_PATHS.workspace, component: WorkspaceApp, launcherVisible: false },
  { id: 'settings', label: '设置', title: '设置', icon: APP_ICON_PATHS.settings, component: SettingsApp, launcherVisible: false },
  { id: 'logs', label: '日志', title: '日志', icon: APP_ICON_PATHS.logs, component: LogViewer, launcherVisible: false },
]

const appRegistryById = new Map(appRegistry.map((app) => [app.id, app]))

export function getRegisteredApp(appId: string): RegisteredApp | undefined {
  return appRegistryById.get(appId)
}

export function getAppMetadata(appId: string): Pick<RegisteredApp, 'id' | 'title' | 'label' | 'icon'> | undefined {
  const app = getRegisteredApp(appId)
  if (!app) return undefined
  return {
    id: app.id,
    title: app.title,
    label: app.label,
    icon: app.icon,
  }
}

export function getLauncherApps(): RegisteredApp[] {
  return appRegistry.filter((app) => app.launcherVisible !== false)
}
