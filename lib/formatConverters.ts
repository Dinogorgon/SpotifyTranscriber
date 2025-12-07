import { TranscriptionResult, TranscriptionSegment } from './types'

export class FormatConverter {
  static toTxt(transcription: TranscriptionResult): string {
    return transcription.text?.trim() || ''
  }

  static toJson(transcription: TranscriptionResult, pretty = true): string {
    if (pretty) {
      return JSON.stringify(transcription, null, 2)
    }
    return JSON.stringify(transcription)
  }

  static formatTimestamp(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const milliseconds = Math.floor((seconds % 1) * 1000)
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(milliseconds).padStart(3, '0')}`
  }

  static formatTimestampVTT(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const milliseconds = Math.floor((seconds % 1) * 1000)
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`
  }

  static toSrt(transcription: TranscriptionResult): string {
    const segments = transcription.segments || []
    
    if (segments.length === 0) {
      const text = transcription.text?.trim()
      if (text) {
        return `1\n00:00:00,000 --> 00:00:10,000\n${text}\n\n`
      }
      return ''
    }
    
    const srtLines: string[] = []
    segments.forEach((segment, index) => {
      const start = segment.start || 0
      const end = segment.end || start + 1
      const text = segment.text?.trim() || ''
      
      const startTime = this.formatTimestamp(start)
      const endTime = this.formatTimestamp(end)
      
      srtLines.push(`${index + 1}\n${startTime} --> ${endTime}\n${text}\n\n`)
    })
    
    return srtLines.join('')
  }

  static toVtt(transcription: TranscriptionResult): string {
    const segments = transcription.segments || []
    const vttLines: string[] = ['WEBVTT\n']
    
    if (segments.length === 0) {
      const text = transcription.text?.trim()
      if (text) {
        vttLines.push('00:00:00.000 --> 00:00:10.000\n')
        vttLines.push(`${text}\n\n`)
      }
      return vttLines.join('')
    }
    
    segments.forEach((segment) => {
      const start = segment.start || 0
      const end = segment.end || start + 1
      const text = segment.text?.trim() || ''
      
      const startTime = this.formatTimestampVTT(start)
      const endTime = this.formatTimestampVTT(end)
      
      vttLines.push(`${startTime} --> ${endTime}\n`)
      vttLines.push(`${text}\n\n`)
    })
    
    return vttLines.join('')
  }

  static toDisplayText(
    transcription: TranscriptionResult,
    width = 96,
    gapThreshold = 1.5
  ): string {
    const segments = transcription.segments || []
    
    if (segments.length === 0) {
      const text = transcription.text?.trim() || ''
      return this.wrapText(text, width)
    }

    const paragraphs: string[] = []
    let current: string[] = []
    let lastEnd: number | null = null

    segments.forEach((segment) => {
      const text = segment.text?.trim() || ''
      if (!text) return

      const start = segment.start || 0
      const end = segment.end || start
      const gap = lastEnd !== null ? start - lastEnd : 0

      if ((gap > gapThreshold && current.length > 0) || 
          (current.join(' ').length > 320)) {
        paragraphs.push(current.join(' ').trim())
        current = [text]
      } else {
        current.push(text)
      }

      lastEnd = end

      if (text.match(/[.!?]$/) && current.join(' ').length > 200) {
        paragraphs.push(current.join(' ').trim())
        current = []
      }
    })

    if (current.length > 0) {
      paragraphs.push(current.join(' ').trim())
    }

    const wrapped = paragraphs
      .filter(p => p)
      .map(p => this.wrapText(p, width))
    
    return wrapped.join('\n\n').trim()
  }

  private static wrapText(text: string, width: number): string {
    const words = text.split(' ')
    const lines: string[] = []
    let currentLine = ''

    words.forEach((word) => {
      if ((currentLine + word).length <= width) {
        currentLine += (currentLine ? ' ' : '') + word
      } else {
        if (currentLine) {
          lines.push(currentLine)
        }
        currentLine = word
      }
    })

    if (currentLine) {
      lines.push(currentLine)
    }

    return lines.join('\n')
  }
}

