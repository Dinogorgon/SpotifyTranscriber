import React from 'react'
import './ProgressBar.css'

function ProgressBar({ message, percent }) {
  return (
    <div className="progress-container">
      <div className="progress-label">{message}</div>
      <div className="progress-bar-wrapper">
        <div 
          className="progress-bar-fill" 
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}

export default ProgressBar

