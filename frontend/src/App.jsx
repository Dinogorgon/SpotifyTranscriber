import React, { useState } from 'react'
import './App.css'
import Header from './components/Header'
import EpisodeInfo from './components/EpisodeInfo'
import Transcript from './components/Transcript'
import Summary from './components/Summary'
import ProgressBar from './components/ProgressBar'
import { transcribeEpisode, getMetadata, downloadAudio } from './services/api'

function App() {
  const [episodeInfo, setEpisodeInfo] = useState(null)
  const [transcription, setTranscription] = useState(null)
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState({ message: 'Ready', percent: 0 })
  const [url, setUrl] = useState('')
  const [backend, setBackend] = useState('faster')
  const [modelSize, setModelSize] = useState('base')
  const [showTimestamps, setShowTimestamps] = useState(false)

  const handleTranscribe = async () => {
    if (!url.trim()) {
      alert('Please enter a Spotify URL')
      return
    }

    setLoading(true)
    setProgress({ message: 'Starting...', percent: 0 })

    try {
      // Step 1: Get metadata
      setProgress({ message: 'Fetching Spotify metadata...', percent: 10 })
      const metadata = await getMetadata(url)
      setEpisodeInfo(metadata)

      // Step 2: Transcribe
      setProgress({ message: `Loading ${backend} Whisper model (${modelSize})...`, percent: 30 })
      
      // Start transcription with progress updates
      let currentProgress = 30
      const result = await transcribeEpisode(url, backend, modelSize, (percent) => {
        currentProgress = 30 + (percent * 0.6)
        setProgress({ 
          message: `Transcribing with ${backend} Whisper (${modelSize})... ${Math.round(percent)}%`, 
          percent: currentProgress
        })
      })

      setProgress({ message: 'Generating AI summary...', percent: 95 })
      setTranscription(result)
      setSummary(result.summary || '')

      setProgress({ message: 'Complete!', percent: 100 })
    } catch (error) {
      alert(`Error: ${error.message}`)
      setProgress({ message: `Error: ${error.message}`, percent: 0 })
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadMP3 = async () => {
    if (!url.trim()) {
      alert('Please enter a Spotify URL')
      return
    }

    try {
      setProgress({ message: 'Downloading MP3...', percent: 0 })
      await downloadAudio(url)
      setProgress({ message: 'Download complete!', percent: 100 })
    } catch (error) {
      alert(`Error: ${error.message}`)
      setProgress({ message: `Error: ${error.message}`, percent: 0 })
    }
  }

  return (
    <div className="app">
      <Header 
        url={url}
        setUrl={setUrl}
        onTranscribe={handleTranscribe}
        loading={loading}
        backend={backend}
        setBackend={setBackend}
        modelSize={modelSize}
        setModelSize={setModelSize}
      />
      
      <ProgressBar message={progress.message} percent={progress.percent} />
      
      <div className="main-content">
        <EpisodeInfo 
          info={episodeInfo}
        />
        
        <Transcript 
          transcription={transcription}
          showTimestamps={showTimestamps}
          setShowTimestamps={setShowTimestamps}
          onDownloadMP3={handleDownloadMP3}
        />
        
        <Summary summary={summary} />
      </div>
    </div>
  )
}

export default App

