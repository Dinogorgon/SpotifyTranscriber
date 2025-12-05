'use client'

import styles from './ProgressBar.module.css'

interface ProgressBarProps {
  message: string
  percent: number
}

export default function ProgressBar({ message, percent }: ProgressBarProps) {
  return (
    <div className={styles.progressContainer}>
      <div className={styles.progressLabel}>{message}</div>
      <div className={styles.progressBarWrapper}>
        <div 
          className={styles.progressBarFill} 
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}

