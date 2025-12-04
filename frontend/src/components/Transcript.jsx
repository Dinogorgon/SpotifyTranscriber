import React, { useMemo } from 'react'
import './Transcript.css'

function Transcript({ transcription, showTimestamps, setShowTimestamps, onDownloadMP3 }) {
  const formattedText = useMemo(() => {
    if (!transcription) return ''

    if (showTimestamps && transcription.segments) {
      // Group segments into chunks
      const chunks = []
      let currentChunk = []
      let lastEnd = null

      transcription.segments.forEach((seg) => {
        const text = seg.text?.trim()
        if (!text) return

        const start = seg.start || 0
        const end = seg.end || start
        const gap = lastEnd !== null ? start - lastEnd : 0

        if ((gap > 1.5 && currentChunk.length > 0) || 
            (text.match(/[.!?]$/) && currentChunk.length > 2)) {
          if (currentChunk.length > 0) {
            chunks.push(currentChunk)
          }
          currentChunk = [seg]
        } else {
          currentChunk.push(seg)
        }

        lastEnd = end
      })

      if (currentChunk.length > 0) {
        chunks.push(currentChunk)
      }

      // Format chunks with timestamps
      return chunks.map((chunk) => {
        const firstSeg = chunk[0]
        const startTime = firstSeg.start || 0
        const mins = Math.floor(startTime / 60)
        const secs = Math.floor(startTime % 60)
        const timestamp = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
        const text = chunk.map(s => s.text?.trim()).filter(Boolean).join(' ')
        
        return { timestamp, text }
      })
    } else {
      // Plain text format
      return transcription.text || ''
    }
  }, [transcription, showTimestamps])

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
    <div className="transcript-panel">
      <div className="transcript-header">
        <h2>Transcript</h2>
        <div className="transcript-actions">
          <button onClick={onDownloadMP3} className="action-btn" title="Download MP3">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="23 7 16 12 23 17 23 7"></polygon>
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
            </svg>
          </button>
          <button onClick={handleCopy} className="action-btn" title="Copy">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
          <button onClick={handleDownload} className="action-btn" title="Download">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </button>
        </div>
      </div>

      <div className="transcript-controls">
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={showTimestamps}
            onChange={(e) => setShowTimestamps(e.target.checked)}
          />
          <span>Include timestamps</span>
        </label>
      </div>

      <div className="transcript-content">
        {!transcription ? (
          <div className="transcript-placeholder">
            <p>Transcription will appear here</p>
          </div>
        ) : Array.isArray(formattedText) ? (
          <div className="transcript-timestamped">
            {formattedText.map((item, idx) => (
              <div key={idx} className="transcript-chunk">
                <span className="timestamp-box">{item.timestamp}</span>
                <span className="transcript-text">{item.text}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="transcript-plain">
            {formattedText.split('\n\n').map((para, idx) => (
              <p key={idx}>{para}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Transcript

