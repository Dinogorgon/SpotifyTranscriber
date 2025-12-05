'use client'

import { useState } from 'react'
import Header from '@/components/Header'
import EpisodeInfo from '@/components/EpisodeInfo'
import Transcript from '@/components/Transcript'
import Summary from '@/components/Summary'
import ProgressBar from '@/components/ProgressBar'
import { EpisodeMetadata, TranscriptionResult } from '@/lib/types'
import styles from './page.module.css'

export default function Home() {
  const [episodeInfo, setEpisodeInfo] = useState<EpisodeMetadata | null>(null)
  const [transcription, setTranscription] = useState<TranscriptionResult | null>(null)
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState({ message: 'Ready', percent: 0 })
  const [url, setUrl] = useState('')
  const [backend, setBackend] = useState<'faster' | 'openai'>('faster')
  const [modelSize, setModelSize] = useState<'tiny' | 'base' | 'small' | 'medium' | 'large'>('base')
  const [showTimestamps, setShowTimestamps] = useState(false)

  const handleTranscribe = async () => {
    if (!url.trim()) {
      alert('Please enter a Spotify URL')
      return
    }

    setLoading(true)
    setProgress({ message: 'Starting...', percent: 0 })

    try {
      // Step 1: Get metadata
      setProgress({ message: 'Fetching Spotify metadata...', percent: 10 })
      const metadataResponse = await fetch(`/api/metadata?spotify_url=${encodeURIComponent(url)}`)
      if (!metadataResponse.ok) {
        throw new Error('Failed to fetch metadata')
      }
      const metadata = await metadataResponse.json()
      setEpisodeInfo(metadata)

      // Step 2: Transcribe
      setProgress({ message: `Loading ${backend} Whisper model (${modelSize})...`, percent: 30 })
      
      const transcribeResponse = await fetch('/api/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spotify_url: url,
          backend,
          model_size: modelSize,
        }),
      })

      if (!transcribeResponse.ok) {
        const error = await transcribeResponse.json()
        throw new Error(error.error || 'Transcription failed')
      }

      setProgress({ message: 'Generating AI summary...', percent: 95 })
      const result = await transcribeResponse.json()
      setTranscription(result)
      setSummary(result.summary || '')

      setProgress({ message: 'Complete!', percent: 100 })
    } catch (error: any) {
      alert(`Error: ${error.message}`)
      setProgress({ message: `Error: ${error.message}`, percent: 0 })
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadMP3 = async () => {
    if (!url.trim()) {
      alert('Please enter a Spotify URL')
      return
    }

    try {
      setProgress({ message: 'Downloading MP3...', percent: 0 })
      const response = await fetch(`/api/download-audio?spotify_url=${encodeURIComponent(url)}`)
      
      if (!response.ok) {
        throw new Error('Failed to download audio')
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      
      const contentDisposition = response.headers.get('content-disposition')
      let filename = 'episode.mp3'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)
      
      setProgress({ message: 'Download complete!', percent: 100 })
    } catch (error: any) {
      alert(`Error: ${error.message}`)
      setProgress({ message: `Error: ${error.message}`, percent: 0 })
    }
  }

  return (
    <div className={styles.app}>
      <Header 
        url={url}
        setUrl={setUrl}
        onTranscribe={handleTranscribe}
        loading={loading}
        backend={backend}
        setBackend={setBackend}
        modelSize={modelSize}
        setModelSize={setModelSize}
      />
      
      <ProgressBar message={progress.message} percent={progress.percent} />
      
      <div className={styles.mainContent}>
        <EpisodeInfo info={episodeInfo} />
        
        <Transcript 
          transcription={transcription}
          showTimestamps={showTimestamps}
          setShowTimestamps={setShowTimestamps}
          onDownloadMP3={handleDownloadMP3}
        />
        
        <Summary summary={summary} />
      </div>
    </div>
  )
}

