import React from 'react'
import './Summary.css'

function Summary({ summary }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(summary)
    alert('Summary copied to clipboard!')
  }

  const handleDownload = () => {
    const blob = new Blob([summary], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'summary.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="summary-panel">
      <div className="summary-header">
        <h2>Summary</h2>
        <div className="summary-actions">
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

      <div className="summary-content">
        {!summary ? (
          <div className="summary-placeholder">
            <p>AI-generated summary will appear here</p>
          </div>
        ) : (
          <div className="summary-text">
            {summary.split('\n\n').map((para, idx) => (
              <p key={idx}>{para}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Summary

