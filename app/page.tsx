'use client'

import { useState } from 'react'
import Header from '@/components/Header'
import EpisodeInfo from '@/components/EpisodeInfo'
import Transcript from '@/components/Transcript'
import Summary from '@/components/Summary'
import ProgressBar from '@/components/ProgressBar'
import Toast from '@/components/Toast'
import { EpisodeMetadata, TranscriptionResult } from '@/lib/types'
import { useToast } from '@/lib/useToast'
import { apiClient } from '@/lib/apiClient'
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
  const [inputMode, setInputMode] = useState<'url' | 'file'>('url')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { toast, showError, showSuccess, showInfo, hideToast } = useToast()

  const handleTranscribe = async () => {
    if (inputMode === 'url' && !url.trim()) {
      showError('Please enter a Spotify URL')
      return
    }

    if (inputMode === 'file' && !selectedFile) {
      showError('Please select a file to upload')
      return
    }

    setLoading(true)
    setProgress({ message: 'Starting...', percent: 0 })

    try {
      let filePath: string | undefined

      if (inputMode === 'file' && selectedFile) {
        // Step 1: Upload file
        setProgress({ message: 'Uploading file...', percent: 10 })
        const uploadResult = await apiClient.uploadFile(selectedFile)
        filePath = uploadResult.file_path

        // Set basic episode info from file
        setEpisodeInfo({
          id: selectedFile.name,
          title: selectedFile.name.replace(/\.[^/.]+$/, ''),
          subtitle: `Uploaded file (${(selectedFile.size / 1024 / 1024).toFixed(2)} MB)`,
        })

        setProgress({ message: 'File uploaded successfully', percent: 20 })
      } else {
        // Step 1: Get metadata for Spotify URL
        setProgress({ message: 'Fetching Spotify metadata...', percent: 10 })
        const metadata = await apiClient.getMetadata(url)
        setEpisodeInfo(metadata)
        setProgress({ message: 'Metadata fetched', percent: 20 })
      }

      // Step 2: Transcribe with streaming progress
      setProgress({ message: `Transcribing with ${backend} Whisper (${modelSize})...`, percent: 30 })
      
      const transcribeResponse = await apiClient.transcribeStream({
        spotify_url: inputMode === 'url' ? url : undefined,
        file_path: inputMode === 'file' ? filePath : undefined,
        backend,
        model_size: modelSize,
      })

      // Parse Server-Sent Events stream
      const reader = transcribeResponse.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      if (!reader) {
        throw new Error('Failed to get response stream')
      }

      let result: any = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'progress') {
                setProgress({ message: data.message, percent: data.percent })
              } else if (data.type === 'error') {
                throw new Error(data.error)
              } else if (data.type === 'result') {
                result = data.data
              }
            } catch (e) {
              // Ignore JSON parse errors for non-data lines
              if (e instanceof SyntaxError) continue
              throw e
            }
          }
        }
      }

      if (!result) {
        throw new Error('No result received from transcription')
      }

      setTranscription(result)
      setSummary(result.summary || '')
      setProgress({ message: 'Complete!', percent: 100 })
      showSuccess('Transcription completed successfully!')
    } catch (error: any) {
      const errorMessage = error.message || 'An unexpected error occurred'
      showError(errorMessage)
      setProgress({ message: `Error: ${errorMessage}`, percent: 0 })
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadMP3 = async () => {
    if (inputMode === 'url' && !url.trim()) {
      showError('Please enter a Spotify URL')
      return
    }

    if (inputMode === 'file') {
      showInfo('MP3 download is only available for Spotify URLs')
      return
    }

    try {
      setProgress({ message: 'Downloading MP3...', percent: 0 })
      const response = await apiClient.downloadAudio(url)
      
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
      showSuccess('MP3 downloaded successfully!')
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to download audio'
      showError(errorMessage)
      setProgress({ message: `Error: ${errorMessage}`, percent: 0 })
    }
  }

  return (
    <div className={styles.app}>
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
      
      <Header 
        url={url}
        setUrl={setUrl}
        onTranscribe={handleTranscribe}
        loading={loading}
        backend={backend}
        setBackend={setBackend}
        modelSize={modelSize}
        setModelSize={setModelSize}
        inputMode={inputMode}
        setInputMode={setInputMode}
        selectedFile={selectedFile}
        setSelectedFile={setSelectedFile}
        showError={showError}
      />
      
      <ProgressBar message={progress.message} percent={progress.percent} />
      
      <div className={styles.mainContent}>
        <EpisodeInfo info={episodeInfo} />
        
        <Transcript 
          transcription={transcription}
          showTimestamps={showTimestamps}
          setShowTimestamps={setShowTimestamps}
          onDownloadMP3={handleDownloadMP3}
          showSuccess={showSuccess}
        />
        
        <Summary summary={summary} showSuccess={showSuccess} />
      </div>
    </div>
  )
}

