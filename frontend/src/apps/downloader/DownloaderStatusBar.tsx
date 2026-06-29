import { useEffect, useState } from 'react'

import { fetchSystemRuntimeMetrics } from '@/api'

const ZERO_SPEED = { text: '0 B/s' }

type DownloaderStatusBarProps = {
  detailOpen: boolean
  onToggleDetail: () => void
}

export function DownloaderStatusBar({ detailOpen, onToggleDetail }: DownloaderStatusBarProps) {
  const [network, setNetwork] = useState({
    upload: ZERO_SPEED,
    download: ZERO_SPEED,
  })

  useEffect(() => {
    let cancelled = false

    async function refreshNetwork() {
      try {
        const metrics = await fetchSystemRuntimeMetrics()
        if (!cancelled && metrics.network) {
          setNetwork({
            upload: normalizeNetworkSpeed(metrics.network.upload),
            download: normalizeNetworkSpeed(metrics.network.download),
          })
        }
      } catch {
        // Keep the last displayed value when the local API is unavailable.
      }
    }

    void refreshNetwork()
    const timer = window.setInterval(() => void refreshNetwork(), 1000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [])

  return (
    <footer className="dl-status">
      <span className="dl-speed">
        ↓ {network.download?.text || '0 B/s'} <span>|</span> ↑ {network.upload?.text || '0 B/s'}
      </span>
      <button type="button" className="dl-task-detail" onClick={onToggleDetail}>
        {detailOpen ? '收起详情' : '任务详情'}
      </button>
    </footer>
  )
}

function normalizeNetworkSpeed(value?: { text?: string }) {
  return { text: value?.text || ZERO_SPEED.text }
}
