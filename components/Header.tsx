'use client'

import { FormEvent, useRef, ChangeEvent } from 'react'
import styles from './Header.module.css'

interface HeaderProps {
  url: string
  setUrl: (url: string) => void
  onTranscribe: () => void
  loading: boolean
  backend: 'faster' | 'openai'
  setBackend: (backend: 'faster' | 'openai') => void
  modelSize: 'tiny' | 'base' | 'small' | 'medium' | 'large'
  setModelSize: (size: 'tiny' | 'base' | 'small' | 'medium' | 'large') => void
  inputMode: 'url' | 'file'
  setInputMode: (mode: 'url' | 'file') => void
  selectedFile: File | null
  setSelectedFile: (file: File | null) => void
  showError: (message: string) => void
}

export default function Header({
  url,
  setUrl,
  onTranscribe,
  loading,
  backend,
  setBackend,
  modelSize,
  setModelSize,
  inputMode,
  setInputMode,
  selectedFile,
  setSelectedFile,
  showError,
}: HeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!loading) {
      onTranscribe()
    }
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    if (file) {
      // Validate file type
      const validTypes = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'video/mp4', 'audio/x-m4a', 'audio/m4a']
      const validExtensions = ['.mp3', '.mp4', '.m4a']
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
      
      if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        showError('Please select an MP3, MP4, or M4A file')
        return
      }

      // Validate file size (1.5 GB = 1,610,612,736 bytes)
      const maxSize = 1610612736
      if (file.size > maxSize) {
        showError(`File size must be less than 1.5 GB. Your file is ${(file.size / 1024 / 1024).toFixed(2)} MB`)
        return
      }

      setSelectedFile(file)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        <h1 className={styles.logo}>Spotify Transcriber</h1>
        
        <div className={styles.inputModeToggle}>
          <button
            type="button"
            className={`${styles.toggleBtn} ${inputMode === 'url' ? styles.toggleBtnActive : ''}`}
            onClick={() => setInputMode('url')}
            disabled={loading}
          >
            URL
          </button>
          <button
            type="button"
            className={`${styles.toggleBtn} ${inputMode === 'file' ? styles.toggleBtnActive : ''}`}
            onClick={() => setInputMode('file')}
            disabled={loading}
          >
            File Upload
          </button>
        </div>

        {inputMode === 'url' ? (
          <form onSubmit={handleSubmit} className={styles.urlForm}>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste a Spotify episode URL..."
              className={styles.urlInput}
              disabled={loading}
            />
            <button 
              type="submit" 
              className={styles.submitBtn}
              disabled={loading}
            >
              →
            </button>
          </form>
        ) : (
          <div className={styles.fileUploadContainer}>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/mpeg,audio/mp3,audio/mp4,video/mp4,audio/x-m4a,audio/m4a,.mp3,.mp4,.m4a"
              onChange={handleFileChange}
              className={styles.fileInput}
              disabled={loading}
            />
            <button
              type="button"
              onClick={handleUploadClick}
              className={styles.uploadBtn}
              disabled={loading}
            >
              {selectedFile ? `📁 ${selectedFile.name.substring(0, 30)}${selectedFile.name.length > 30 ? '...' : ''}` : '📤 Upload MP3/MP4/M4A'}
            </button>
            {selectedFile && (
              <button
                type="button"
                onClick={onTranscribe}
                className={styles.submitBtn}
                disabled={loading}
              >
                →
              </button>
            )}
          </div>
        )}

        <div className={styles.headerOptions}>
          <div className={styles.optionGroup}>
            <label>Engine:</label>
            <select 
              value={backend} 
              onChange={(e) => setBackend(e.target.value as 'faster' | 'openai')}
              disabled={loading}
              className={styles.optionSelect}
            >
              <option value="faster">Faster</option>
              <option value="openai">Accurate</option>
            </select>
          </div>
          
          <div className={styles.optionGroup}>
            <label>Model:</label>
            <select 
              value={modelSize} 
              onChange={(e) => setModelSize(e.target.value as any)}
              disabled={loading}
              className={styles.optionSelect}
            >
              <option value="tiny">Tiny</option>
              <option value="base">Base</option>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  )
}

