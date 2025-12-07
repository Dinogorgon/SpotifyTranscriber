/**
 * API Client for communicating with the backend service
 * Uses NEXT_PUBLIC_BACKEND_URL environment variable or defaults to localhost
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface TranscribeRequest {
  spotify_url?: string
  file_path?: string
  backend: 'faster' | 'openai'
  model_size: 'tiny' | 'base' | 'small' | 'medium' | 'large'
}

export interface EpisodeMetadata {
  id: string
  title: string
  subtitle?: string
  description?: string
  cover_image?: string
  release_date?: string
  url?: string
}

export interface UploadResponse {
  file_path: string
  file_name: string
  file_size: number
}

export const apiClient = {
  /**
   * Get Spotify episode metadata
   */
  async getMetadata(spotifyUrl: string): Promise<EpisodeMetadata> {
    const response = await fetch(`${BACKEND_URL}/api/metadata?spotify_url=${encodeURIComponent(spotifyUrl)}`)
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.error || 'Failed to fetch metadata')
    }
    return response.json()
  },

  /**
   * Upload a file to the backend
   */
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.error || 'File upload failed')
    }

    return response.json()
  },

  /**
   * Transcribe audio with streaming progress
   */
  async transcribeStream(request: TranscribeRequest): Promise<Response> {
    const response = await fetch(`${BACKEND_URL}/api/transcribe-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.error || 'Transcription failed')
    }

    return response
  },

  /**
   * Download audio file from Spotify
   */
  async downloadAudio(spotifyUrl: string): Promise<Response> {
    const response = await fetch(`${BACKEND_URL}/api/download-audio?spotify_url=${encodeURIComponent(spotifyUrl)}`)
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || error.error || 'Failed to download audio')
    }
    return response
  },

  /**
   * Get proxy URL for an image to avoid CORS issues
   */
  proxyImage(imageUrl: string): string {
    return `${BACKEND_URL}/api/proxy-image?image_url=${encodeURIComponent(imageUrl)}`
  },
}

