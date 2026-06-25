import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { getActiveTasks, getWeeklyHistory } from '@/api'
import { mergeTasks } from '@/apps/downloader/helpers'
import type { DownloadTask } from '@/apps/downloader/types'

export function useDownloaderTaskData() {
  const [tasks, setTasks] = useState<DownloadTask[]>([])
  const [historyTasks, setHistoryTasks] = useState<DownloadTask[]>([])
  const [optimisticTasks, setOptimisticTasks] = useState<DownloadTask[]>([])
  const loadingRef = useRef(false)
  const historyLoadingRef = useRef(false)

  const fetchTasks = useCallback(async () => {
    if (loadingRef.current) return
    loadingRef.current = true
    try {
      const activeRes = await getActiveTasks()
      // v2 API returns array directly, not {tasks: [...]}
      const activeTasks: DownloadTask[] = Array.isArray(activeRes) ? activeRes : (activeRes.tasks || [])

      // Map v2 API response to DownloadTask format
      const mappedTasks = activeTasks.map((task: any) => ({
        id: task.id || task.task_id,
        name: task.title || 'Untitled',
        type: 'download' as const,
        status: task.status || 'pending',
        progress: task.progress || 0,
        stage: task.stage || 'queued',
        created_at: Date.now() / 1000, // v2 doesn't return created_at yet
        source_url: task.source_url || '',
        title: task.title || '',
        output_files: task.output_files || [],
        error: task.error || null,
        result: task.output_files && task.output_files.length > 0 ? { files: task.output_files } : undefined,
      }))

      mappedTasks.sort((a, b) => b.created_at - a.created_at)
      setTasks(mappedTasks)
    } catch {
      // Keep the last successful list when polling fails.
    } finally {
      loadingRef.current = false
    }
  }, [])

  const fetchHistoryTasks = useCallback(async () => {
    if (historyLoadingRef.current) return
    historyLoadingRef.current = true
    try {
      const historyRes = await getWeeklyHistory()
      // v2 API returns same endpoint as active tasks for now
      const history: DownloadTask[] = Array.isArray(historyRes) ? historyRes : (historyRes.tasks || [])

      const mappedHistory = history.map((task: any) => ({
        id: task.id || task.task_id,
        name: task.title || 'Untitled',
        type: 'download' as const,
        status: task.status || 'pending',
        progress: task.progress || 0,
        stage: task.stage || 'queued',
        created_at: Date.now() / 1000,
        source_url: task.source_url || '',
        title: task.title || '',
        output_files: task.output_files || [],
        error: task.error || null,
        result: task.output_files && task.output_files.length > 0 ? { files: task.output_files } : undefined,
      }))

      mappedHistory.sort((a, b) => b.created_at - a.created_at)
      setHistoryTasks(mappedHistory)
    } catch {
      // Keep the last successful list when polling fails.
    } finally {
      historyLoadingRef.current = false
    }
  }, [])

  useEffect(() => {
    void fetchTasks()
    const interval = setInterval(() => {
      void fetchTasks()
    }, 2000)
    return () => clearInterval(interval)
  }, [fetchTasks])

  useEffect(() => {
    void fetchHistoryTasks()
  }, [fetchHistoryTasks])

  useEffect(() => {
    setOptimisticTasks((prev) =>
      prev.filter(
        (task) => !tasks.some((activeTask) => activeTask.id === task.id) && !historyTasks.some((historyTask) => historyTask.id === task.id),
      ),
    )
  }, [historyTasks, tasks])

  const queueTasks = useMemo(() => mergeTasks(optimisticTasks, tasks), [optimisticTasks, tasks])
  /** history 需在合并时覆盖 queue：避免乐观任务或旧 active 占位（无 result）盖住历史里的完整落盘字段 */
  const mergedTasks = useMemo(() => mergeTasks(historyTasks, queueTasks), [historyTasks, queueTasks])

  const refreshLists = useCallback(async () => {
    await Promise.all([fetchTasks(), fetchHistoryTasks()])
  }, [fetchHistoryTasks, fetchTasks])

  return {
    tasks,
    historyTasks,
    queueTasks,
    mergedTasks,
    fetchHistoryTasks,
    refreshLists,
    setOptimisticTasks,
  }
}
