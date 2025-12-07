import React, { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import AudioRecorder from './components/AudioRecorder'
import { RESUME_QUESTIONS } from './constants/questions'
import Navbar from './components/home/Navbar'
import HeroSection from './components/home/HeroSection'
import LanguageSelector from './components/home/LanguageSelector'
import QuestionFlowCard from './components/QuestionFlowCard'
import ResumeResultCard from './components/ResumeResultCard'
import Footer from './components/home/Footer'
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
      document.documentElement.classList.add('dark')
    } else {
      document.body.classList.remove('dark-mode')
      document.documentElement.classList.remove('dark')
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
    <div className="min-h-screen flex flex-col font-sans selection:bg-neon-purple selection:text-white">
      <Navbar darkMode={darkMode} toggleDarkMode={() => setDarkMode(!darkMode)} />

      <AnimatePresence mode="wait">
        {/* Main Content Area */}
        {currentStep === 'welcome' && (
          <motion.main
            key="welcome"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            transition={{ duration: 0.5 }}
            className="flex-grow flex items-center justify-center relative p-6 pt-24 min-h-[90vh]"
          >
            <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center z-10">
              {/* Left Column: Text & CTA */}
              <HeroSection onStart={handleStartQA} />

              {/* Right Column: Language Card */}
              <div className="flex justify-center lg:justify-end">
                <LanguageSelector
                  selectedLanguage={selectedLanguage}
                  setSelectedLanguage={setSelectedLanguage}
                  languages={languages}
                />
              </div>
            </div>
          </motion.main>
        )}

        {/* Legacy/Existing Views wrapped in a clean container */}
        {currentStep !== 'welcome' && (
          <motion.main
            key={currentStep} // 'qa' or 'profile'
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="flex-grow w-full max-w-screen-xl mx-auto px-4 py-24"
          >
            {/* Q&A Screen */}
            {currentStep === 'qa' && (
              <QuestionFlowCard
                currentQuestion={currentQuestion}
                currentIndex={currentQuestionIndex}
                totalQuestions={RESUME_QUESTIONS.length}
                audioControl={{
                  isPlaying: isPlayingAudio,
                  onPlayPause: handlePauseAudio,
                  onReplay: handleReplayAudio,
                  audioAvailable,
                  error: audioError,
                  questionAudio
                }}
                recordingControl={{
                  isProcessing: isProcessingAnswer,
                  statusMessage,
                  onRecordingComplete: handleRecordingComplete,
                  onRecordStart: stopQuestionAudio
                }}
                textControl={{
                  textAnswer,
                  setTextAnswer,
                  onSubmit: handleTextSubmit
                }}
                onSkip={handleSkipQuestion}
                onRestart={handleRestart}
                error={error}
              />
            )}

            {/* Profile Display Screen */}
            {currentStep === 'profile' && (
              <ResumeResultCard
                profile={finalProfile}
                isBuilding={isBuildingProfile}
                statusMessage={statusMessage}
                onRestart={handleRestart}
                apiBaseUrl={API_BASE_URL}
              />
            )}
          </motion.main>
        )}
      </AnimatePresence>

      <Footer />
    </div>
  )
}

export default App
