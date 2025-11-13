import React, { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [transcription, setTranscription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError('')
      setTranscription('')
    }
  }

  const handleTranscribe = async () => {
    if (!file) {
      setError('Please select an audio file')
      return
    }

    setLoading(true)
    setError('')
    setTranscription('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/transcribe', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setTranscription(data.text)
    } catch (err) {
      setError(`Error: ${err.message}`)
      console.error('Transcription error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h1>🎙️ JobSathi Transcriber</h1>
        <p className="subtitle">Convert audio to text using AI</p>
        
        <div className="upload-section">
          <input
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            disabled={loading}
            id="fileInput"
          />
          <label htmlFor="fileInput" className="upload-label">
            {file ? `Selected: ${file.name}` : 'Click to select audio file'}
          </label>
        </div>

        <button
          onClick={handleTranscribe}
          disabled={!file || loading}
          className="transcribe-btn"
        >
          {loading ? '⏳ Transcribing...' : '🚀 Transcribe'}
        </button>

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        {transcription && (
          <div className="result-section">
            <h2>Transcription Result</h2>
            <div className="transcription-text">
              {transcription}
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(transcription)
              }}
              className="copy-btn"
            >
              📋 Copy Text
            </button>
          </div>
        )}

        <div className="info-section">
          <p>✨ Features:</p>
          <ul>
            <li>Support for WAV, MP3, and other audio formats</li>
            <li>Hindi language support</li>
            <li>Fast AI-powered transcription</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default App
