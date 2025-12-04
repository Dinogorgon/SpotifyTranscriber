import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const getMetadata = async (spotifyUrl) => {
  const response = await api.get('/api/metadata', {
    params: { spotify_url: spotifyUrl }
  })
  return response.data
}

export const transcribeEpisode = async (spotifyUrl, backend, modelSize, progressCallback) => {
  // For now, we'll use a simple POST request
  // In the future, we could implement WebSocket for real-time progress
  try {
    // Simulate progress updates (in real implementation, use WebSocket)
    if (progressCallback) {
      // Start progress simulation
      const progressInterval = setInterval(() => {
        // This will be updated by actual progress if WebSocket is implemented
      }, 100)
      
      const response = await api.post('/api/transcribe', {
        spotify_url: spotifyUrl,
        backend: backend,
        model_size: modelSize
      })
      
      clearInterval(progressInterval)
      if (progressCallback) progressCallback(100)
      
      return response.data
    } else {
      const response = await api.post('/api/transcribe', {
        spotify_url: spotifyUrl,
        backend: backend,
        model_size: modelSize
      })
      return response.data
    }
  } catch (error) {
    throw new Error(error.response?.data?.detail || error.message || 'Transcription failed')
  }
}

export const downloadAudio = async (spotifyUrl) => {
  const response = await api.get('/api/download-audio', {
    params: { spotify_url: spotifyUrl },
    responseType: 'blob'
  })
  
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  
  // Try to get filename from Content-Disposition header
  const contentDisposition = response.headers['content-disposition']
  let filename = 'episode.mp3'
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
    if (filenameMatch) {
      filename = filenameMatch[1]
    }
  }
  
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export const exportTranscription = async (text, segments, formatType) => {
  const response = await api.post('/api/export', {
    text: text,
    segments: segments,
    format_type: formatType
  }, {
    responseType: 'blob'
  })
  
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `transcription.${formatType}`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

