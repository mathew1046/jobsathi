import React, { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Browser-compatible translation using MyMemory API (free, no key required)
const translateText = async (text, sourceLang, targetLang = 'en') => {
  if (!text || sourceLang === targetLang) return text
  
  try {
    const response = await fetch(
      `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${sourceLang}|${targetLang}`
    )
    const data = await response.json()
    
    if (data.responseStatus === 200 && data.responseData) {
      return data.responseData.translatedText
    }
    throw new Error('Translation failed')
  } catch (err) {
    console.error('Translation error:', err)
    return text
  }
}

const DEFAULT_LANGUAGES = [
  { code: 'hi', label: 'Hindi' },
  { code: 'bn', label: 'Bengali' },
  { code: 'ta', label: 'Tamil' },
  { code: 'te', label: 'Telugu' },
  { code: 'ml', label: 'Malayalam' },
  { code: 'mr', label: 'Marathi' },
  { code: 'gu', label: 'Gujarati' },
  { code: 'pa', label: 'Punjabi' },
  { code: 'or', label: 'Odia' },
  { code: 'as', label: 'Assamese' },
  { code: 'en', label: 'English' }
]

const FEATURE_CHIPS = [
  { icon: '🌈', text: 'Aurora-grade UI' },
  { icon: '🧠', text: 'Chunked IndicTrans' },
  { icon: '🎧', text: 'Conformer ASR' }
]

const PROCESS_STEPS = [
  'Upload audio',
  'Conformer decoding',
  'Chunk & translate',
  'English transcript ready'
]

function App() {
  const [file, setFile] = useState(null)
  const [transcription, setTranscription] = useState('')
  const [originalText, setOriginalText] = useState('')
  const [detectedLanguage, setDetectedLanguage] = useState('')
  const [chunkCount, setChunkCount] = useState(0)
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES)
  const [selectedLanguage, setSelectedLanguage] = useState(DEFAULT_LANGUAGES[0].code)
  const [languageLabel, setLanguageLabel] = useState(DEFAULT_LANGUAGES[0].label)
  const [languagesLoading, setLanguagesLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        setLanguagesLoading(true)
        const response = await fetch(`${API_BASE_URL}/languages`)
        if (!response.ok) throw new Error('Failed to load language list')
        const payload = await response.json()
        const available = Array.isArray(payload.languages) ? payload.languages : []
        if (available.length) {
          setLanguages(available)
          const defaultLang = available.find((lang) => lang.code === 'hi') || available[0]
          setSelectedLanguage(defaultLang.code)
          setLanguageLabel(defaultLang.label)
        } else {
          setLanguages(DEFAULT_LANGUAGES)
        }
      } catch (err) {
        console.error('Language load error:', err)
        setLanguages(DEFAULT_LANGUAGES)
      } finally {
        setLanguagesLoading(false)
      }
    }

    fetchLanguages()
  }, [])

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSet(e.dataTransfer.files[0])
    }
  }

  const handleFileSet = (selectedFile) => {
    if (selectedFile && selectedFile.type.startsWith('audio/')) {
      setFile(selectedFile)
      setError('')
      setTranscription('')
      setOriginalText('')
      setDetectedLanguage('')
    } else {
      setError('Please select a valid audio file')
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSet(selectedFile)
    }
  }

  const handleTranscribe = async () => {
    if (!file) {
      setError('Please select an audio file')
      return
    }

    if (!selectedLanguage) {
      setError('Please choose a source language')
      return
    }

    setLoading(true)
    setError('')
    setTranscription('')
    setOriginalText('')
    setDetectedLanguage('')
    setChunkCount(0)

    try {
      const formData = new FormData()
      formData.append('audio', file)
      formData.append('source_language', selectedLanguage)

      const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const payload = await response.json()
      const data = payload.data || {}
      const originalText = data.original_text || ''
      
      setOriginalText(originalText)
      setDetectedLanguage(data.language_label || data.detected_language || 'Unknown')

      // Translate using MyMemory free API
      if (originalText && selectedLanguage !== 'en') {
        try {
          const translated = await translateText(originalText, selectedLanguage, 'en')
          setTranscription(translated)
        } catch (translateErr) {
          console.error('Translation error:', translateErr)
          setError('Transcription succeeded but translation failed. Showing original text.')
          setTranscription(originalText)
        }
      } else {
        setTranscription(originalText)
      }
      
      setChunkCount(1)
    } catch (err) {
      setError(`${err.message}`)
      console.error('Transcription error:', err)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(transcription)
    const btn = document.querySelector('.copy-btn')
    if (!btn) return
    const originalText = btn.textContent
    btn.textContent = '✓ Copied!'
    setTimeout(() => {
      btn.textContent = originalText
    }, 2000)
  }

  const handleLanguageChange = (e) => {
    const code = e.target.value
    setSelectedLanguage(code)
    const meta = languages.find((lang) => lang.code === code)
    setLanguageLabel(meta?.label || 'Selected')
  }

  return (
    <div className="app-container">
      <div className="background-animation">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>
      
      <div className="content-wrapper">
        <div className="header">
          <div className="logo">
            <span className="logo-icon">🎙️</span>
            <h1>JobSathi</h1>
          </div>
          <p className="tagline">AI4Bharat Powered Transcription</p>
          <div className="tech-badge">Manual language control • Chunked IndicTrans2 Translation</div>
          <div className="feature-chip-row">
            {FEATURE_CHIPS.map(({ icon, text }) => (
              <span key={text} className="feature-chip">
                {icon} {text}
              </span>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="selector-row">
            <div>
              <p className="selector-heading">Source Language</p>
              <p className="selector-subheading">Choose the language spoken in your audio</p>
            </div>
            <select
              className="language-select"
              value={selectedLanguage}
              onChange={handleLanguageChange}
              disabled={languagesLoading}
            >
              {languagesLoading && (
                <option value={selectedLanguage}>Loading…</option>
              )}
              {!languagesLoading && languages.length === 0 && (
                <option value="">Unavailable</option>
              )}
              {languages.map(({ code, label }) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div 
            className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput').click()}
          >
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              disabled={loading}
              id="fileInput"
              style={{ display: 'none' }}
            />
            
            {!file ? (
              <>
                <div className="upload-icon">📁</div>
                <p className="upload-text">Drop your audio file here</p>
                <p className="upload-subtext">or click to browse</p>
                <div className="supported-formats">
                  <span>WAV</span>
                  <span>MP3</span>
                  <span>M4A</span>
                  <span>FLAC</span>
                </div>
                <p className="language-pill">Current language: {languageLabel}</p>
              </>
            ) : (
              <>
                <div className="file-icon">🎵</div>
                <p className="file-name">{file.name}</p>
                <p className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <p className="language-pill subtle">Source: {languageLabel}</p>
              </>
            )}
          </div>

          <button
            onClick={handleTranscribe}
            disabled={!file || loading}
            className={`transcribe-btn ${loading ? 'loading' : ''}`}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Processing...
              </>
            ) : (
              <>
                <span className="btn-icon">⚡</span>
                Transcribe Audio
              </>
            )}
          </button>

          {error && (
            <div className="message error-message">
              <span className="message-icon">❌</span>
              {error}
            </div>
          )}

          {transcription && (
            <div className="result-container">
              {originalText && detectedLanguage !== 'English' && (
                <>
                  <div className="result-header">
                    <h3>Original ({detectedLanguage})</h3>
                  </div>
                  <div className="transcription-box original">
                    {originalText}
                  </div>
                </>
              )}
              
              <div className="result-header">
                <h3>English Translation</h3>
                {detectedLanguage && (
                  <span className="duration-badge">{detectedLanguage}</span>
                )}
              </div>
              <div className="transcription-box">
                {transcription}
              </div>
              <div className="info-grid">
                <div className="stat-card">
                  <p className="stat-label">Chunks processed</p>
                  <p className="stat-value">{chunkCount || 1}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">Language</p>
                  <p className="stat-value">{languageLabel}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-label">File size</p>
                  <p className="stat-value">{((file?.size || 0) / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button onClick={copyToClipboard} className="copy-btn">
                <span className="btn-icon">📋</span>
                Copy to Clipboard
              </button>
            </div>
          )}

          <div className="process-flow">
            {PROCESS_STEPS.map((step, index) => (
              <div key={step} className="process-step">
                <span className="step-index">{index + 1}</span>
                <p>{step}</p>
              </div>
            ))}
          </div>
        </div>

        <footer className="footer">
          <p>Powered by AI4Bharat IndicWhisper & IndicTrans2 • Built with ❤️</p>
        </footer>
      </div>
    </div>
  )
}

export default App
