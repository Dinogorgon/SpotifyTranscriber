'use client'

import { EpisodeMetadata } from '@/lib/types'
import styles from './EpisodeInfo.module.css'

interface EpisodeInfoProps {
  info: EpisodeMetadata | null
}

export default function EpisodeInfo({ info }: EpisodeInfoProps) {
  const formatDate = (dateString?: string): string => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateString
    }
  }

  return (
    <div className={styles.episodeInfo}>
      <div className={styles.episodeInfoHeader}>
        <h2>Episode Info</h2>
      </div>
      
      <div className={styles.episodeInfoContent}>
        {!info ? (
          <div className={styles.episodeInfoPlaceholder}>
            <div className={styles.coverPlaceholder}>
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
            </div>
            <p>Enter a Spotify URL to get started</p>
          </div>
        ) : (
          <>
            <div className={styles.coverImageContainer}>
              {info.cover_image ? (
                <img 
                  src={`/api/proxy-image?image_url=${encodeURIComponent(info.cover_image)}`}
                  alt={info.title || 'Episode cover'}
                  className={styles.episodeCover}
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    target.style.display = 'none'
                    const placeholder = target.parentElement?.querySelector(`.${styles.coverPlaceholder}`) as HTMLElement
                    if (placeholder) placeholder.style.display = 'flex'
                  }}
                />
              ) : null}
              <div 
                className={styles.coverPlaceholder} 
                style={{ display: info.cover_image ? 'none' : 'flex' }}
              >
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </div>
            </div>
            
            <h3 className={styles.episodeTitle}>{info.title || 'Untitled Episode'}</h3>
            
            {info.subtitle && (
              <p className={styles.episodeSubtitle}>{info.subtitle}</p>
            )}
            
            {info.release_date && (
              <p className={styles.episodeDate}>{formatDate(info.release_date)}</p>
            )}
            
            <div className={styles.episodeDescription}>
              <h4>Description</h4>
              {info.description ? (
                <p>{info.description}</p>
              ) : (
                <p className={styles.descriptionPlaceholder}>No description available</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

