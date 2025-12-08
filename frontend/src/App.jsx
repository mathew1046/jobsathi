import React, { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import './App.css'
import LoadingScreen from './components/LoadingScreen'
import QuestionFlowCard from './components/QuestionFlowCard'
import ResumeResultCard from './components/ResumeResultCard'
import Navbar from './components/home/Navbar'
import HeroSection from './components/home/HeroSection'
import LanguageSelector from './components/home/LanguageSelector'
import LanguageSelectionModal from './components/home/LanguageSelectionModal'
import Footer from './components/home/Footer'
import { RESUME_QUESTIONS } from './constants/questions'
import uiStrings from './constants/ui_strings.json'
import LANG_MAP from './constants/lang'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const DEFAULT_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'as', label: 'Assamese' },
  { code: 'bn', label: 'Bengali' },
  { code: 'brx', label: 'Bodo' },
  { code: 'doi', label: 'Dogri' },
  { code: 'gom', label: 'Konkani' },
  { code: 'gu', label: 'Gujarati' },
  { code: 'hi', label: 'Hindi' },
  { code: 'kn', label: 'Kannada' },
  { code: 'ks', label: 'Kashmiri (Arabic)' },
  { code: 'ks-deva', label: 'Kashmiri (Devanagari)' },
  { code: 'mai', label: 'Maithili' },
  { code: 'ml', label: 'Malayalam' },
  { code: 'mr', label: 'Marathi' },
  { code: 'mni', label: 'Meitei (Bengali script)' },
  { code: 'mni-mtei', label: 'Meitei (Meitei script)' },
  { code: 'npi', label: 'Nepali' },
  { code: 'or', label: 'Odia' },
  { code: 'pa', label: 'Punjabi' },
  { code: 'sa', label: 'Sanskrit' },
  { code: 'sat', label: 'Santali' },
  { code: 'sd', label: 'Sindhi (Arabic)' },
  { code: 'sd-deva', label: 'Sindhi (Devanagari)' },
  { code: 'ta', label: 'Tamil' },
  { code: 'te', label: 'Telugu' },
  { code: 'ur', label: 'Urdu' },
]

const defaultStrings = uiStrings

const App = () => {
  const [selectedLanguage, setSelectedLanguage] = useState('en')
  const [translations, setTranslations] = useState(defaultStrings)
  const [translatedQuestions, setTranslatedQuestions] = useState(RESUME_QUESTIONS)
  const [isTranslating, setIsTranslating] = useState(false)
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES)
  const [darkMode, setDarkMode] = useState(false)
  const [questionAudio, setQuestionAudio] = useState(null)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [audioAvailable, setAudioAvailable] = useState(false)
  const [audioError, setAudioError] = useState('')
  const [currentStep, setCurrentStep] = useState('welcome')
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [qaResponses, setQaResponses] = useState([])
  const [error, setError] = useState('')
  const [textAnswer, setTextAnswer] = useState('')
  const [isBuildingProfile, setIsBuildingProfile] = useState(false)
  const [finalProfile, setFinalProfile] = useState(null)
  const [isSearchingJobs, setIsSearchingJobs] = useState(false)
  const [jobs, setJobs] = useState([])
  const [showJobs, setShowJobs] = useState(false)
  const [isLanguageSelected, setIsLanguageSelected] = useState(false)

  const resetQuestionAudio = () => {
    if (questionAudio) {
      questionAudio.pause()
      questionAudio.currentTime = 0
    }
    setQuestionAudio(null)
    setIsPlayingAudio(false)
    setAudioAvailable(false)
    setAudioError('')
  }

  useEffect(() => {
    const applyTranslations = async () => {
      if (!selectedLanguage) return

      const bundle = LANG_MAP[selectedLanguage]
      if (!bundle) {
        setTranslations(defaultStrings)
        setTranslatedQuestions(RESUME_QUESTIONS)
        setIsTranslating(false)
        return
      }

      setIsTranslating(true)
      try {
        const mapped = { ...defaultStrings, ...bundle }

        const newQuestions = RESUME_QUESTIONS.map(q => ({
          ...q,
          question: mapped[`q_${q.id}`] || q.question,
          prompt: mapped[`p_${q.id}`] || q.prompt,
        }))

        setTranslations(mapped)
        setTranslatedQuestions(newQuestions)
      } catch (error) {
        console.error('Translation load error:', error)
        setTranslations(defaultStrings)
        setTranslatedQuestions(RESUME_QUESTIONS)
      } finally {
        setIsTranslating(false)
      }
    }

    applyTranslations()
  }, [selectedLanguage])

  const t = (key) => translations[key] || defaultStrings[key] || key

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
    setLanguages(DEFAULT_LANGUAGES)
  }, [])

  useEffect(() => {
    if (currentStep === 'qa' && currentQuestionIndex >= 0) {
      loadQuestionAudio()
    }
  }, [currentQuestionIndex, selectedLanguage, currentStep])

  useEffect(() => {
    return () => {
      if (questionAudio) {
        questionAudio.pause()
        questionAudio.currentTime = 0
      }
    }
  }, [questionAudio])

  const loadQuestionAudio = async () => {
    resetQuestionAudio()

    if (currentQuestionIndex < 0 || currentQuestionIndex >= translatedQuestions.length) return

    const translatedQuestion = translatedQuestions[currentQuestionIndex]
    const fallbackEnglish = RESUME_QUESTIONS[currentQuestionIndex]
    const textToSend = `${translatedQuestion?.question || ''} ${translatedQuestion?.prompt || ''}`.trim() || fallbackEnglish.question

    try {
      setAudioAvailable(false)
      setAudioError('')

      const params = new URLSearchParams({
        text: textToSend,
        language: selectedLanguage || 'en',
      })

      const resp = await fetch(`${API_BASE_URL}/get-question-audio?${params.toString()}`)

      if (!resp.ok) throw new Error('TTS request failed')

      const blob = await resp.blob()
      const audioUrl = URL.createObjectURL(blob)
      const audio = new Audio(audioUrl)

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

      audio.play().catch(() => {
        setIsPlayingAudio(false)
      })
      setIsPlayingAudio(true)

    } catch (err) {
      console.log('Audio load error:', err)
      setQuestionAudio(null)
      setAudioAvailable(false)
      setAudioError('TTS not available for this language')
      setIsPlayingAudio(false)
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
    stopQuestionAudio()
    setIsProcessingAnswer(true)
    setError('')
    setStatusMessage('Transcribing your answer...')

    try {
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

      const newResponse = {
        question_id: currentQuestion.id,
        field: currentQuestion.field,
        question: currentQuestion.question,
        transcript: transcript,
        extracted_data: llmData.data || {}
      }

      const updatedResponses = [...qaResponses, newResponse]
      setQaResponses(updatedResponses)

      if (currentQuestionIndex < RESUME_QUESTIONS.length - 1) {
        resetQuestionAudio()
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setStatusMessage('')
        setTextAnswer('')
      } else {
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

  const buildFinalProfile = async () => {
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
    stopQuestionAudio()
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
        resetQuestionAudio()
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
      resetQuestionAudio()
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

  const handleLanguageSelect = (langCode) => {
    setSelectedLanguage(langCode)
    setIsLanguageSelected(true)
  }

  if (!isLanguageSelected) {
    return (
      <LanguageSelectionModal
        languages={languages}
        onSelectLanguage={handleLanguageSelect}
      />
    )
  }

  if (isTranslating) {
    return <LoadingScreen message="Translating the experience for you..." />
  }

  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-neon-purple selection:text-white">
      <Navbar darkMode={darkMode} toggleDarkMode={() => setDarkMode(!darkMode)} t={t} />

      <AnimatePresence mode="wait">
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
              <HeroSection onStart={handleStartQA} t={t} />

              <div className="flex justify-center lg:justify-end">
                <LanguageSelector
                  selectedLanguage={selectedLanguage}
                  setSelectedLanguage={setSelectedLanguage}
                  languages={languages}
                  t={t}
                />
              </div>
            </div>
          </motion.main>
        )}

        {currentStep !== 'welcome' && (
          <motion.main
            key={currentStep}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="flex-grow w-full max-w-screen-xl mx-auto px-4 py-24"
          >
            {currentStep === 'qa' && (
              <QuestionFlowCard
                key={translatedQuestions[currentQuestionIndex]?.id || currentQuestionIndex}
                currentQuestion={translatedQuestions[currentQuestionIndex]}
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
                t={t}
              />
            )}

            {currentStep === 'profile' && (
              <ResumeResultCard
                profile={finalProfile}
                isBuilding={isBuildingProfile}
                statusMessage={statusMessage}
                onRestart={handleRestart}
                apiBaseUrl={API_BASE_URL}
                onSearchJobs={handleSearchJobs}
                isSearchingJobs={isSearchingJobs}
                jobs={jobs}
                showJobs={showJobs}
                t={t}
              />
            )}
          </motion.main>
        )}
      </AnimatePresence>

      <Footer t={t} />
    </div>
  )
}

export default App
