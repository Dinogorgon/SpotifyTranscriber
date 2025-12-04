import React from 'react'
import './EpisodeInfo.css'

function EpisodeInfo({ info }) {
  const formatDate = (dateString) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateString
    }
  }

  return (
    <div className="episode-info">
      <div className="episode-info-header">
        <h2>Episode Info</h2>
      </div>
      
      <div className="episode-info-content">
        {!info ? (
          <div className="episode-info-placeholder">
            <div className="cover-placeholder">
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
            {/* Cover Image - Always show placeholder or image */}
            <div className="cover-image-container">
              {info.cover_image ? (
                <img 
                  src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/proxy-image?image_url=${encodeURIComponent(info.cover_image)}`}
                  alt={info.title || 'Episode cover'}
                  className="episode-cover"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    const placeholder = e.target.parentElement.querySelector('.cover-placeholder')
                    if (placeholder) placeholder.style.display = 'flex'
                  }}
                />
              ) : null}
              <div 
                className="cover-placeholder" 
                style={{ display: info.cover_image ? 'none' : 'flex' }}
              >
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </div>
            </div>
            
            {/* Title */}
            <h3 className="episode-title">{info.title || 'Untitled Episode'}</h3>
            
            {/* Subtitle */}
            {info.subtitle && (
              <p className="episode-subtitle">{info.subtitle}</p>
            )}
            
            {/* Release Date */}
            {info.release_date && (
              <p className="episode-date">{formatDate(info.release_date)}</p>
            )}
            
            {/* Description - Always show section */}
            <div className="episode-description">
              <h4>Description</h4>
              {info.description ? (
                <p>{info.description}</p>
              ) : (
                <p className="description-placeholder">No description available</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default EpisodeInfo
