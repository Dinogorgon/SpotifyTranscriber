'use client'

import ReactMarkdown from 'react-markdown'
import styles from './Summary.module.css'

interface SummaryProps {
  summary: string
  showSuccess: (message: string) => void
}

export default function Summary({ summary, showSuccess }: SummaryProps) {
  const handleCopy = () => {
    navigator.clipboard.writeText(summary)
    showSuccess('Summary copied to clipboard!')
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
    <div className={styles.summaryPanel}>
      <div className={styles.summaryHeader}>
        <h2>Summary</h2>
        <div className={styles.summaryActions}>
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

      <div className={styles.summaryContent}>
        {!summary ? (
          <div className={styles.summaryPlaceholder}>
            <p>AI-generated summary will appear here</p>
          </div>
        ) : (
          <div className={styles.summaryText}>
            <ReactMarkdown
              components={{
                h2: ({node, ...props}) => <h2 className={styles.markdownH2} {...props} />,
                h3: ({node, ...props}) => <h3 className={styles.markdownH3} {...props} />,
                ul: ({node, ...props}) => <ul className={styles.markdownList} {...props} />,
                ol: ({node, ...props}) => <ol className={styles.markdownList} {...props} />,
                li: ({node, ...props}) => <li className={styles.markdownListItem} {...props} />,
                p: ({node, ...props}) => <p className={styles.markdownParagraph} {...props} />,
                strong: ({node, ...props}) => <strong className={styles.markdownStrong} {...props} />,
              }}
            >
              {summary}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

