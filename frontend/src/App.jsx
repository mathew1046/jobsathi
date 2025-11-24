import React, { useState, useEffect } from 'react'
import AudioRecorder from './components/AudioRecorder'
import { RESUME_QUESTIONS } from './constants/questions'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

function App() {
  // UI State
  const [darkMode, setDarkMode] = useState(false)
  const [currentStep, setCurrentStep] = useState('welcome') // welcome, qa, profile
  const [selectedLanguage, setSelectedLanguage] = useState('hi')
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES)

  // Q&A State
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [qaResponses, setQaResponses] = useState([])
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false)
  const [textAnswer, setTextAnswer] = useState('')
  const [sessionId, setSessionId] = useState(null)

  // Profile State
  const [finalProfile, setFinalProfile] = useState(null)
  const [isBuildingProfile, setIsBuildingProfile] = useState(false)

  // Job Search State
  const [jobs, setJobs] = useState([])
  const [isSearchingJobs, setIsSearchingJobs] = useState(false)
  const [showJobs, setShowJobs] = useState(false)

  // Error & Status
  const [error, setError] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  // Audio TTS State
  const [questionAudio, setQuestionAudio] = useState(null)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [audioAvailable, setAudioAvailable] = useState(true)
  const [audioError, setAudioError] = useState('')

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }, [darkMode])

  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/languages`)
        if (response.ok) {
          const payload = await response.json()
          const available = Array.isArray(payload.languages) ? payload.languages : []
          if (available.length) {
            setLanguages(available)
          }
        }
      } catch (err) {
        console.error('Language load error:', err)
      }
    }
    fetchLanguages()
  }, [])

  // Load question audio when question changes or language changes
  useEffect(() => {
    if (currentStep === 'qa' && currentQuestionIndex >= 0) {
      loadQuestionAudio()
    }
  }, [currentQuestionIndex, selectedLanguage, currentStep])

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (questionAudio) {
        questionAudio.pause()
        questionAudio.currentTime = 0
      }
    }
  }, [questionAudio])

  const loadQuestionAudio = async () => {
    // Stop any currently playing audio
    if (questionAudio) {
      questionAudio.pause()
      questionAudio.currentTime = 0
    }

    const currentQuestion = RESUME_QUESTIONS[currentQuestionIndex]
    const audioPath = `${API_BASE_URL}/audio/${selectedLanguage}/q${currentQuestion.id}.mp3`

    try {
      // Check if audio file exists
      const response = await fetch(audioPath, { method: 'HEAD' })
      
      if (response.ok) {
        const audio = new Audio(audioPath)
        
        audio.addEventListener('ended', () => {
          setIsPlayingAudio(false)
        })
        
        audio.addEventListener('error', () => {
          setAudioAvailable(false)
          setAudioError('TTS not available for this language')
        })
        
        setQuestionAudio(audio)
        setAudioAvailable(true)
        setAudioError('')
        
        // Auto-play the question audio
        audio.play().catch(() => {
          setIsPlayingAudio(false)
        })
        setIsPlayingAudio(true)
      } else {
        setQuestionAudio(null)
        setAudioAvailable(false)
        setAudioError('TTS not available for this language')
      }
    } catch (err) {
      console.log('Audio load error:', err)
      setQuestionAudio(null)
      setAudioAvailable(false)
      setAudioError('TTS not available for this language')
    }
  }

  const handleReplayAudio = () => {
    if (questionAudio && audioAvailable) {
      questionAudio.currentTime = 0
      questionAudio.play().then(() => {
        setIsPlayingAudio(true)
      }).catch((err) => {
        console.error('Replay error:', err)
        setIsPlayingAudio(false)
      })
    }
  }

  const stopQuestionAudio = () => {
    if (questionAudio && isPlayingAudio) {
      questionAudio.pause()
      questionAudio.currentTime = 0
      setIsPlayingAudio(false)
    }
  }

  const handlePauseAudio = () => {
    if (questionAudio && audioAvailable) {
      if (isPlayingAudio) {
        questionAudio.pause()
        setIsPlayingAudio(false)
      } else {
        questionAudio.play().then(() => {
          setIsPlayingAudio(true)
        }).catch((err) => {
          console.error('Play error:', err)
          setIsPlayingAudio(false)
        })
      }
    }
  }

  const handleStartQA = async () => {
    try {
      // Create a new session
      const response = await fetch(`${API_BASE_URL}/start_session`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to start session')
      }
      
      const data = await response.json()
      setSessionId(data.session_id)
      console.log('Session started:', data.session_id)
      
      setCurrentStep('qa')
      setCurrentQuestionIndex(0)
      setQaResponses([])
      setError('')
      setTextAnswer('')
    } catch (err) {
      console.error('Session start error:', err)
      setError('Failed to start session. Please try again.')
    }
  }

  const handleRecordingComplete = async (audioFile) => {
    stopQuestionAudio() // Stop audio when recording completes
    setIsProcessingAnswer(true)
    setError('')
    setStatusMessage('Transcribing your answer...')

    try {
      // Step 1: Transcribe the audio
      const formData = new FormData()
      formData.append('audio', audioFile)
      formData.append('source_language', selectedLanguage)

      const transcribeResponse = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
      })

      if (!transcribeResponse.ok) {
        const errorData = await transcribeResponse.json()
        throw new Error(errorData.detail || 'Transcription failed')
      }

      const transcribeData = await transcribeResponse.json()
      const transcript = transcribeData.data?.original_text || ''

      if (!transcript.trim()) {
        throw new Error('No speech detected. Please try again.')
      }

      setStatusMessage('Extracting information...')

      // Step 2: Extract structured data from the transcript
      const currentQuestion = RESUME_QUESTIONS[currentQuestionIndex]
      const llmResponse = await fetch(`${API_BASE_URL}/ask_llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          transcript: transcript,
          question: currentQuestion.question,
          field: currentQuestion.field,
          question_id: currentQuestion.id
        })
      })

      if (!llmResponse.ok) {
        const errorData = await llmResponse.json()
        throw new Error(errorData.detail || 'Failed to process answer')
      }

      const llmData = await llmResponse.json()

      // Store the Q&A response
      const newResponse = {
        question_id: currentQuestion.id,
        field: currentQuestion.field,
        question: currentQuestion.question,
        transcript: transcript,
        extracted_data: llmData.data || {}
      }

      const updatedResponses = [...qaResponses, newResponse]
      setQaResponses(updatedResponses)

      // Move to next question or finish
      if (currentQuestionIndex < RESUME_QUESTIONS.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setStatusMessage('')
        setTextAnswer('')
      } else {
        // All questions answered, build profile
        await buildFinalProfile(updatedResponses)
      }

    } catch (err) {
      console.error('Answer processing error:', err)
      setError(err.message || 'Failed to process your answer. Please try again.')
    } finally {
      setIsProcessingAnswer(false)
      if (currentQuestionIndex < RESUME_QUESTIONS.length - 1) {
        setStatusMessage('')
      }
    }
  }

  const buildFinalProfile = async (responses) => {
    setIsBuildingProfile(true)
    setStatusMessage('Building your ATS-optimized resume...')
    setCurrentStep('profile')

    try {
      const response = await fetch(`${API_BASE_URL}/build_profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to build profile')
      }

      const data = await response.json()
      setFinalProfile(data.profile)
      
      // Store PDF filename for download
      if (data.pdf_filename) {
        setFinalProfile(prev => ({ ...prev, pdf_filename: data.pdf_filename }))
      }
      
      setStatusMessage('Resume created successfully!')

    } catch (err) {
      console.error('Profile building error:', err)
      setError(err.message || 'Failed to build profile')
    } finally {
      setIsBuildingProfile(false)
    }
  }

  const handleSearchJobs = async () => {
    if (!finalProfile) {
      setError('Profile not available for job search')
      return
    }

    setIsSearchingJobs(true)
    setError('')
    setStatusMessage('Searching for relevant jobs...')

    try {
      const response = await fetch(`${API_BASE_URL}/search_jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ profile: finalProfile })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Job search failed')
      }

      const data = await response.json()
      setJobs(data.jobs || [])
      setShowJobs(true)
      setStatusMessage(`Found ${data.count} relevant jobs!`)

    } catch (err) {
      console.error('Job search error:', err)
      setError(err.message || 'Failed to search jobs')
    } finally {
      setIsSearchingJobs(false)
    }
  }

  const handleTextSubmit = async () => {
    stopQuestionAudio() // Stop audio when submitting text
    if (!textAnswer.trim()) {
      setError('Please enter an answer or use voice recording')
      return
    }

    setIsProcessingAnswer(true)
    setError('')
    setStatusMessage('Processing your answer...')

    try {
      const currentQuestion = RESUME_QUESTIONS[currentQuestionIndex]
      const llmResponse = await fetch(`${API_BASE_URL}/ask_llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          transcript: textAnswer,
          question: currentQuestion.question,
          field: currentQuestion.field,
          question_id: currentQuestion.id
        })
      })

      if (!llmResponse.ok) {
        const errorData = await llmResponse.json()
        throw new Error(errorData.detail || 'Failed to process answer')
      }

      const llmData = await llmResponse.json()

      const newResponse = {
        question_id: currentQuestion.id,
        field: currentQuestion.field,
        question: currentQuestion.question,
        transcript: textAnswer,
        extracted_data: llmData.data || {}
      }

      const updatedResponses = [...qaResponses, newResponse]
      setQaResponses(updatedResponses)

      if (currentQuestionIndex < RESUME_QUESTIONS.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setStatusMessage('')
        setTextAnswer('')
      } else {
        await buildFinalProfile(updatedResponses)
      }

    } catch (err) {
      console.error('Text answer processing error:', err)
      setError(err.message || 'Failed to process your answer. Please try again.')
    } finally {
      setIsProcessingAnswer(false)
    }
  }

  const handleSkipQuestion = () => {
    const currentQuestion = RESUME_QUESTIONS[currentQuestionIndex]
    const skippedResponse = {
      question_id: currentQuestion.id,
      field: currentQuestion.field,
      question: currentQuestion.question,
      transcript: '',
      extracted_data: { value: null, skipped: true }
    }

    const updatedResponses = [...qaResponses, skippedResponse]
    setQaResponses(updatedResponses)
    setTextAnswer('')

    if (currentQuestionIndex < RESUME_QUESTIONS.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      buildFinalProfile(updatedResponses)
    }
  }

  const handleRestart = () => {
    setCurrentStep('welcome')
    setCurrentQuestionIndex(0)
    setQaResponses([])
    setFinalProfile(null)
    setError('')
    setStatusMessage('')
  }

  const downloadProfile = () => {
    const blob = new Blob([JSON.stringify(finalProfile, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resume_${finalProfile?.name?.replace(/\s+/g, '_') || 'profile'}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const currentQuestion = RESUME_QUESTIONS[currentQuestionIndex]
  const progress = ((currentQuestionIndex + 1) / RESUME_QUESTIONS.length) * 100

  return (
    <div className={`app-container ${darkMode ? 'dark' : ''}`}>
      <div className="background-animation">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      <button
        className="dark-mode-toggle"
        onClick={() => setDarkMode(!darkMode)}
        aria-label="Toggle dark mode"
      >
        {darkMode ? '☀️' : '🌙'}
      </button>

      <div className="content-wrapper">
        {/* Welcome Screen */}
        {currentStep === 'welcome' && (
          <div className="welcome-screen">
            <div className="logo-large">
              <span className="logo-icon-large">🎙️</span>
              <h1 className="title-large">JobSathi</h1>
            </div>
            <p className="subtitle">Voice-Powered Resume Builder</p>
            <p className="description">
              Create your professional resume in {RESUME_QUESTIONS.length} simple voice responses.
              Powered by AI4Bharat speech recognition and AI intelligence.
            </p>

            <div className="language-selector-card">
              <h3>Select Your Language</h3>
              <p className="selector-hint">Choose the language you'll speak in</p>
              <select
                className="language-select-large"
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
              >
                {languages.map(({ code, label }) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <button className="start-button" onClick={handleStartQA}>
              <span className="btn-icon">🚀</span>
              Start Building Resume
            </button>

            <div className="features-grid">
              <div className="feature-item">
                <span className="feature-icon">🎤</span>
                <h4>Voice First</h4>
                <p>Speak naturally in your language</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🧠</span>
                <h4>AI Powered</h4>
                <p>Smart extraction & formatting</p>
              </div>
              <div className="feature-item">
                <span className="feature-icon">⚡</span>
                <h4>Fast & Easy</h4>
                <p>Complete in under 10 minutes</p>
              </div>
            </div>
          </div>
        )}

        {/* Q&A Screen */}
        {currentStep === 'qa' && (
          <div className="qa-screen">
            <div className="qa-header">
              <h2 className="qa-title">Building Your Resume</h2>
              <div className="progress-container">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                </div>
                <p className="progress-text">
                  Question {currentQuestionIndex + 1} of {RESUME_QUESTIONS.length}
                </p>
              </div>
            </div>

            <div className="question-card">
              <div className="question-header-row">
                <div className="question-text-wrapper">
                  <div className="question-number">Q{currentQuestionIndex + 1}</div>
                  <h3 className="question-text">{currentQuestion.question}</h3>
                </div>
                {audioAvailable && questionAudio && (
                  <div className="audio-controls">
                    <button 
                      className="audio-control-button pause-button"
                      onClick={handlePauseAudio}
                      title={isPlayingAudio ? "Pause audio" : "Play audio"}
                    >
                      {isPlayingAudio ? '⏸️' : '▶️'}
                    </button>
                    <button 
                      className="audio-control-button replay-button"
                      onClick={handleReplayAudio}
                      title="Replay question audio"
                    >
                      🔁
                    </button>
                  </div>
                )}
              </div>
              {audioError && !audioAvailable && (
                <div className="audio-status-message">
                  <span className="info-icon">ℹ️</span>
                  <span>{audioError}</span>
                </div>
              )}
              <p className="question-prompt">{currentQuestion.prompt}</p>

              {!isProcessingAnswer && !statusMessage && (
                <>
                  <div className="input-method-divider">
                    <span>Record with voice</span>
                  </div>

                  <AudioRecorder
                    onRecordingComplete={handleRecordingComplete}
                    onRecordStart={stopQuestionAudio}
                    disabled={isProcessingAnswer}
                  />

                  <div className="input-method-divider">
                    <span>Or type your answer</span>
                  </div>

                  <div className="text-input-container">
                    <textarea
                      className="text-answer-input"
                      placeholder="Type your answer here..."
                      value={textAnswer}
                      onChange={(e) => setTextAnswer(e.target.value)}
                      rows={4}
                      disabled={isProcessingAnswer}
                    />
                    <button
                      className="submit-text-button"
                      onClick={handleTextSubmit}
                      disabled={isProcessingAnswer || !textAnswer.trim()}
                    >
                      <span className="btn-icon">📝</span>
                      Submit Answer
                    </button>
                  </div>

                  <button className="skip-button" onClick={handleSkipQuestion}>
                    Skip Question
                  </button>
                </>
              )}

              {(isProcessingAnswer || statusMessage) && (
                <div className="processing-indicator">
                  <div className="spinner-large"></div>
                  <p>{statusMessage}</p>
                </div>
              )}

              {error && (
                <div className="error-box">
                  <span className="error-icon">⚠️</span>
                  <p>{error}</p>
                  <button className="retry-button" onClick={() => setError('')}>
                    Try Again
                  </button>
                </div>
              )}
            </div>

            <div className="qa-navigation">
              <button
                className="nav-button secondary"
                onClick={handleRestart}
                disabled={isProcessingAnswer}
              >
                Start Over
              </button>
            </div>
          </div>
        )}

        {/* Profile Display Screen */}
        {currentStep === 'profile' && (
          <div className="profile-screen">
            <div className="profile-header">
              <h2 className="profile-title">
                {isBuildingProfile ? 'Creating Your ATS Resume...' : 'Your ATS-Optimized Resume'}
              </h2>
              {finalProfile && finalProfile.pdf_filename && !isBuildingProfile && (
                <a
                  href={`${API_BASE_URL}/download_resume/${finalProfile.pdf_filename}`}
                  download
                  className="download-pdf-button"
                >
                  📄 Download PDF Resume
                </a>
              )}
            </div>

            {isBuildingProfile && (
              <div className="processing-indicator">
                <div className="spinner-large"></div>
                <p>{statusMessage}</p>
              </div>
            )}

            {finalProfile && !isBuildingProfile && (
              <>
                <div className="profile-card">
                  <div className="profile-section">
                    <h3 className="section-title">Personal Information</h3>
                    <div className="info-grid">
                      {finalProfile.name && (
                        <div className="info-item">
                          <span className="info-label">Name:</span>
                          <span className="info-value">{String(finalProfile.name)}</span>
                        </div>
                      )}
                      {finalProfile.role && (
                        <div className="info-item">
                          <span className="info-label">Role:</span>
                          <span className="info-value">{String(finalProfile.role)}</span>
                        </div>
                      )}
                      {finalProfile.email && (
                        <div className="info-item">
                          <span className="info-label">Email:</span>
                          <span className="info-value">{String(finalProfile.email)}</span>
                        </div>
                      )}
                      {finalProfile.phone && (
                        <div className="info-item">
                          <span className="info-label">Phone:</span>
                          <span className="info-value">{String(finalProfile.phone)}</span>
                        </div>
                      )}
                      {finalProfile.location && (
                        <div className="info-item">
                          <span className="info-label">Location:</span>
                          <span className="info-value">{String(finalProfile.location)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {finalProfile.summary && (
                    <div className="profile-section">
                      <h3 className="section-title">Summary</h3>
                      <p className="section-content">{String(finalProfile.summary)}</p>
                    </div>
                  )}

                  {finalProfile.experience_details && (
                    <div className="profile-section">
                      <h3 className="section-title">Experience</h3>
                      {finalProfile.experience_years && (
                        <p className="experience-years">{String(finalProfile.experience_years)} years</p>
                      )}
                      {Array.isArray(finalProfile.experience_details) ? (
                        finalProfile.experience_details.map((exp, idx) => (
                          <div key={idx} className="experience-item">
                            <h4 className="exp-role">{typeof exp === 'object' ? (exp.role || 'Role') : String(exp)}</h4>
                            {typeof exp === 'object' && (
                              <>
                                <p className="exp-company">{String(exp.company || 'Company')} • {String(exp.duration || 'Duration')}</p>
                                <p className="exp-description">{String(exp.description || '')}</p>
                              </>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="section-content">{typeof finalProfile.experience_details === 'string' ? finalProfile.experience_details : JSON.stringify(finalProfile.experience_details)}</p>
                      )}
                    </div>
                  )}

                  {finalProfile.skills && (
                    <div className="profile-section">
                      <h3 className="section-title">Skills</h3>
                      <div className="tags-container">
                        {(Array.isArray(finalProfile.skills)
                          ? finalProfile.skills
                          : finalProfile.skills.split(',').map(s => s.trim())
                        ).map((skill, idx) => (
                          <span key={idx} className="tag">{typeof skill === 'object' ? JSON.stringify(skill) : String(skill)}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {finalProfile.education && (
                    <div className="profile-section">
                      <h3 className="section-title">Education</h3>
                      {Array.isArray(finalProfile.education) ? (
                        finalProfile.education.map((edu, idx) => (
                          <div key={idx} className="education-item">
                            <h4 className="edu-degree">{typeof edu === 'object' ? (edu.degree || 'Degree') : String(edu)}</h4>
                            {typeof edu === 'object' && (
                              <p className="edu-institution">{String(edu.institution || 'Institution')} • {String(edu.year || 'Year')}</p>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="section-content">{typeof finalProfile.education === 'string' ? finalProfile.education : JSON.stringify(finalProfile.education)}</p>
                      )}
                    </div>
                  )}

                  {finalProfile.certifications && (
                    <div className="profile-section">
                      <h3 className="section-title">Certifications</h3>
                      {Array.isArray(finalProfile.certifications) ? (
                        <ul className="cert-list">
                          {finalProfile.certifications.map((cert, idx) => (
                            <li key={idx}>{typeof cert === 'object' ? JSON.stringify(cert) : String(cert)}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="section-content">{typeof finalProfile.certifications === 'string' ? finalProfile.certifications : JSON.stringify(finalProfile.certifications)}</p>
                      )}
                    </div>
                  )}

                  {finalProfile.projects && (
                    <div className="profile-section">
                      <h3 className="section-title">Notable Projects</h3>
                      <p className="section-content">{String(finalProfile.projects)}</p>
                    </div>
                  )}

                  {finalProfile.languages && (
                    <div className="profile-section">
                      <h3 className="section-title">Languages</h3>
                      {Array.isArray(finalProfile.languages) ? (
                        <div className="tags-container">
                          {finalProfile.languages.map((lang, idx) => (
                            <span key={idx} className="tag">
                              {typeof lang === 'object' 
                                ? `${lang.language || lang.name || 'Language'}${lang.proficiency ? ` (${lang.proficiency})` : ''}` 
                                : String(lang)
                              }
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="section-content">{typeof finalProfile.languages === 'string' ? finalProfile.languages : JSON.stringify(finalProfile.languages)}</p>
                      )}
                    </div>
                  )}

                  {finalProfile.links && (
                    <div className="profile-section">
                      <h3 className="section-title">Professional Links</h3>
                      {typeof finalProfile.links === 'object' && !Array.isArray(finalProfile.links) ? (
                        <div className="links-container">
                          {Object.entries(finalProfile.links).map(([key, value]) => (
                            value && (
                              <div key={key} className="link-item">
                                <span className="link-label">{String(key)}:</span>
                                <a href={String(value).startsWith('http') ? String(value) : `https://${String(value)}`} target="_blank" rel="noopener noreferrer" className="link-value">{String(value)}</a>
                              </div>
                            )
                          ))}
                        </div>
                      ) : (
                        <p className="section-content">{typeof finalProfile.links === 'string' ? finalProfile.links : JSON.stringify(finalProfile.links)}</p>
                      )}
                    </div>
                  )}

                  {finalProfile.extras && (
                    <div className="profile-section">
                      <h3 className="section-title">Additional Information</h3>
                      {typeof finalProfile.extras === 'object' && !Array.isArray(finalProfile.extras) ? (
                        <div className="extras-container">
                          {Object.entries(finalProfile.extras).map(([key, value]) => (
                            <div key={key} className="extra-item">
                              <span className="extra-label">{String(key)}:</span>
                              <span className="extra-value">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="section-content">{typeof finalProfile.extras === 'string' ? finalProfile.extras : JSON.stringify(finalProfile.extras)}</p>
                      )}
                    </div>
                  )}
                </div>

                <div className="profile-actions">
                  <button className="action-button primary" onClick={downloadProfile}>
                    <span className="btn-icon">💾</span>
                    Download JSON
                  </button>
                  <button className="action-button secondary" onClick={handleRestart}>
                    <span className="btn-icon">🔄</span>
                    Create Another
                  </button>
                  <button
                    className="action-button secondary"
                    onClick={handleSearchJobs}
                    disabled={isSearchingJobs}
                  >
                    {isSearchingJobs ? 'Searching Jobs...' : '🔍 Find Relevant Jobs'}
                  </button>
                </div>

                {/* Job Listings Section */}
                {showJobs && (
                  <div className="jobs-section">
                    <h3 className="section-title">
                      Relevant Job Openings ({jobs.length})
                    </h3>
                    {isSearchingJobs && (
                      <div className="processing-indicator">
                        <div className="spinner"></div>
                        <p>{statusMessage}</p>
                      </div>
                    )}
                    {!isSearchingJobs && jobs.length === 0 && (
                      <p className="no-jobs">No jobs found matching your profile. Try updating your resume or check back later.</p>
                    )}
                    {!isSearchingJobs && jobs.length > 0 && (
                      <div className="jobs-grid">
                        {jobs.map((job, index) => (
                          <div key={index} className="job-card">
                            <div className="job-header">
                              <h4 className="job-title">{job.title}</h4>
                              <span className="job-source">{job.source}</span>
                            </div>
                            <div className="job-info">
                              <p className="job-company">
                                <span className="job-icon">🏢</span>
                                {job.company}
                              </p>
                              <p className="job-location">
                                <span className="job-icon">📍</span>
                                {job.location}
                              </p>
                              {job.salary && job.salary !== 'Not specified' && (
                                <p className="job-salary">
                                  <span className="job-icon">💰</span>
                                  {job.salary}
                                </p>
                              )}
                              {job.relevance_score && (
                                <p className="job-relevance">
                                  <span className="job-icon">⭐</span>
                                  Match: {job.relevance_score}/30
                                </p>
                              )}
                            </div>
                            {job.description && (
                              <p className="job-description">{job.description}</p>
                            )}
                            {job.url && (
                              <a
                                href={job.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="apply-button"
                              >
                                Apply Now →
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {error && !isBuildingProfile && (
              <div className="error-box">
                <span className="error-icon">⚠️</span>
                <p>{error}</p>
                <button className="retry-button" onClick={handleRestart}>
                  Start Over
                </button>
              </div>
            )}
          </div>
        )}

        <footer className="footer">
          <p>Powered by AI4Bharat & OpenRouter AI • Built with ❤️ for Job Seekers</p>
        </footer>
      </div>
    </div>
  )
}

export default App
