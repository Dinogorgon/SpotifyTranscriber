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
    try {
      const response = await fetch(`${BACKEND_URL}/api/transcribe-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = 'Transcription failed'
        try {
          const error = await response.json()
          errorMessage = error.detail || error.error || errorMessage
        } catch {
          // If JSON parsing fails, check status code
          if (response.status === 500 || response.status === 503) {
            errorMessage = 'Server error - this may indicate a memory limit issue. Please try a smaller model or shorter audio.'
          } else {
            errorMessage = `Transcription failed with status ${response.status}`
          }
        }
        throw new Error(errorMessage)
      }

      return response
    } catch (error: any) {
      // Handle network errors that might indicate server crash
      if (error instanceof TypeError && error.message.includes('fetch')) {
        // Network error - could be server crash due to memory
        throw new Error('Connection failed - server may have encountered a memory limit. Please try a smaller model (tiny or base) or a shorter audio file.')
      }
      throw error
    }
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

