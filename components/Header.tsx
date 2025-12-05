'use client'

import { FormEvent } from 'react'
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
}: HeaderProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!loading) {
      onTranscribe()
    }
  }

  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        <h1 className={styles.logo}>Spotify Transcriber</h1>
        
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

