import React from 'react'
import './Header.css'

function Header({ url, setUrl, onTranscribe, loading, backend, setBackend, modelSize, setModelSize }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!loading) {
      onTranscribe()
    }
  }

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="logo">Spotify Transcriber</h1>
        
        <form onSubmit={handleSubmit} className="url-form">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste a Spotify episode URL..."
            className="url-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading}
          >
            →
          </button>
        </form>

        <div className="header-options">
          <div className="option-group">
            <label>Engine:</label>
            <select 
              value={backend} 
              onChange={(e) => setBackend(e.target.value)}
              disabled={loading}
              className="option-select"
            >
              <option value="faster">Faster</option>
              <option value="openai">Accurate</option>
            </select>
          </div>
          
          <div className="option-group">
            <label>Model:</label>
            <select 
              value={modelSize} 
              onChange={(e) => setModelSize(e.target.value)}
              disabled={loading}
              className="option-select"
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

export default Header

