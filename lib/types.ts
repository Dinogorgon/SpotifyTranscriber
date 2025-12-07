export interface EpisodeMetadata {
  id: string
  title: string
  subtitle?: string
  description?: string
  cover_image?: string
  release_date?: string
  url?: string
}

export interface TranscriptionSegment {
  id: number
  start: number
  end: number
  text: string
}

export interface TranscriptionResult {
  text: string
  segments: TranscriptionSegment[]
  language: string
  duration: number
  summary?: string
}

export interface TranscribeRequest {
  spotify_url?: string
  file_path?: string
  backend: 'faster' | 'openai'
  model_size: 'tiny' | 'base' | 'small' | 'medium' | 'large'
}

export interface ProgressCallback {
  (percent: number): void
}

