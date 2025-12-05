'use client'

import { useMemo } from 'react'
import { TranscriptionResult } from '@/lib/types'
import styles from './Transcript.module.css'

interface TranscriptProps {
  transcription: TranscriptionResult | null
  showTimestamps: boolean
  setShowTimestamps: (show: boolean) => void
  onDownloadMP3: () => void
}

interface Chunk {
  timestamp: string
  text: string
}

export default function Transcript({
  transcription,
  showTimestamps,
  setShowTimestamps,
  onDownloadMP3,
}: TranscriptProps) {
  const formattedText = useMemo(() => {
    if (!transcription) return ''

    if (showTimestamps && transcription.segments) {
      const chunks: Chunk[] = []
      let currentChunk: typeof transcription.segments = []
      let lastEnd: number | null = null

      transcription.segments.forEach((seg) => {
        const text = seg.text?.trim()
        if (!text) return

        const start = seg.start || 0
        const end = seg.end || start
        const gap = lastEnd !== null ? start - lastEnd : 0

        if ((gap > 1.5 && currentChunk.length > 0) || 
            (text.match(/[.!?]$/) && currentChunk.length > 2)) {
          if (currentChunk.length > 0) {
            chunks.push({
              timestamp: formatTime(currentChunk[0].start || 0),
              text: currentChunk.map(s => s.text?.trim()).filter(Boolean).join(' '),
            })
          }
          currentChunk = [seg]
        } else {
          currentChunk.push(seg)
        }

        lastEnd = end
      })

      if (currentChunk.length > 0) {
        chunks.push({
          timestamp: formatTime(currentChunk[0].start || 0),
          text: currentChunk.map(s => s.text?.trim()).filter(Boolean).join(' '),
        })
      }

      return chunks
    } else {
      return transcription.text || ''
    }
  }, [transcription, showTimestamps])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  const handleCopy = () => {
    let textToCopy = ''
    if (Array.isArray(formattedText)) {
      textToCopy = formattedText.map(item => 
        showTimestamps ? `[${item.timestamp}] ${item.text}` : item.text
      ).join('\n\n')
    } else {
      textToCopy = formattedText
    }

    navigator.clipboard.writeText(textToCopy)
    alert('Transcript copied to clipboard!')
  }

  const handleDownload = () => {
    let textToDownload = ''
    if (Array.isArray(formattedText)) {
      textToDownload = formattedText.map(item => 
        showTimestamps ? `[${item.timestamp}] ${item.text}` : item.text
      ).join('\n\n')
    } else {
      textToDownload = formattedText
    }

    const blob = new Blob([textToDownload], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'transcript.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.transcriptPanel}>
      <div className={styles.transcriptHeader}>
        <h2>Transcript</h2>
        <div className={styles.transcriptActions}>
          <button onClick={onDownloadMP3} className={styles.actionBtn} title="Download MP3">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="23 7 16 12 23 17 23 7"></polygon>
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
            </svg>
          </button>
          <button onClick={handleCopy} className={styles.actionBtn} title="Copy">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
          <button onClick={handleDownload} className={styles.actionBtn} title="Download">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </button>
        </div>
      </div>

      <div className={styles.transcriptControls}>
        <label className={styles.toggleSwitch}>
          <input
            type="checkbox"
            checked={showTimestamps}
            onChange={(e) => setShowTimestamps(e.target.checked)}
          />
          <span>Include timestamps</span>
        </label>
      </div>

      <div className={styles.transcriptContent}>
        {!transcription ? (
          <div className={styles.transcriptPlaceholder}>
            <p>Transcription will appear here</p>
          </div>
        ) : Array.isArray(formattedText) ? (
          <div className={styles.transcriptTimestamped}>
            {formattedText.map((item, idx) => (
              <div key={idx} className={styles.transcriptChunk}>
                <span className={styles.timestampBox}>{item.timestamp}</span>
                <span className={styles.transcriptText}>{item.text}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.transcriptPlain}>
            {formattedText.split('\n\n').map((para, idx) => (
              <p key={idx}>{para}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

