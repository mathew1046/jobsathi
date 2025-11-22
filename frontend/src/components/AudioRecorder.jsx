import React, { useState, useRef, useEffect } from 'react'
import './AudioRecorder.css'

const AudioRecorder = ({ onRecordingComplete, onRecordStart, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioURL, setAudioURL] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const canvasRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const animationFrameRef = useRef(null)
  const audioPlayerRef = useRef(null)
  const streamRef = useRef(null)

  // Cleanup function
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  // Draw waveform on canvas
  const drawWaveform = () => {
    if (!analyserRef.current || !canvasRef.current) return

    const canvas = canvasRef.current
    const canvasCtx = canvas.getContext('2d')
    const analyser = analyserRef.current
    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw)
      analyser.getByteTimeDomainData(dataArray)

      canvasCtx.fillStyle = 'rgba(18, 18, 18, 0.8)'
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height)

      canvasCtx.lineWidth = 2
      canvasCtx.strokeStyle = '#667eea'
      canvasCtx.beginPath()

      const sliceWidth = canvas.width / bufferLength
      let x = 0

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * canvas.height) / 2

        if (i === 0) {
          canvasCtx.moveTo(x, y)
        } else {
          canvasCtx.lineTo(x, y)
        }

        x += sliceWidth
      }

      canvasCtx.lineTo(canvas.width, canvas.height / 2)
      canvasCtx.stroke()
    }

    draw()
  }

  const startRecording = async () => {
    // Call onRecordStart callback if provided
    if (onRecordStart) {
      onRecordStart()
    }
    
    try {
      // Check if mediaDevices is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support audio recording. Please use Chrome, Edge, or Firefox.')
      }

      // Request microphone permission with explicit constraints
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      streamRef.current = stream

      // Setup Web Audio API for waveform visualization
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()
      audioContextRef.current = audioContext
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      analyserRef.current = analyser

      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)

      // Start drawing waveform
      drawWaveform()
      
      // Use webm format with opus codec for better compatibility
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType })
        const file = new File([blob], 'recording.webm', { type: mimeType })
        const url = URL.createObjectURL(blob)
        setAudioURL(url)
        
        // Stop waveform animation
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
        }
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

    } catch (error) {
      console.error('Error accessing microphone:', error)
      
      let errorMessage = 'Could not access microphone. '
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage += 'Permission was denied. Please:\n\n' +
                       '1. Click the camera/microphone icon in your browser address bar\n' +
                       '2. Allow microphone access for this site\n' +
                       '3. Refresh the page and try again'
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        errorMessage += 'No microphone found. Please connect a microphone and try again.'
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        errorMessage += 'Microphone is already in use by another application. Please close other apps and try again.'
      } else if (error.name === 'OverconstrainedError') {
        errorMessage += 'Could not satisfy microphone constraints. Please try a different microphone.'
      } else if (error.name === 'SecurityError') {
        errorMessage += 'Access denied for security reasons. Make sure you are using HTTPS or localhost.'
      } else {
        errorMessage += error.message || 'Unknown error occurred. Please try refreshing the page.'
      }
      
      alert(errorMessage)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleSubmitRecording = () => {
    if (audioURL && chunksRef.current.length > 0) {
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const blob = new Blob(chunksRef.current, { type: mimeType })
      const file = new File([blob], 'recording.webm', { type: mimeType })
      onRecordingComplete(file)
    }
  }

  const handleReRecord = () => {
    // Clean up previous recording
    if (audioURL) {
      URL.revokeObjectURL(audioURL)
    }
    setAudioURL(null)
    setIsPlaying(false)
    setRecordingTime(0)
    chunksRef.current = []
    
    // Start new recording
    startRecording()
  }

  const togglePlayPause = () => {
    if (!audioPlayerRef.current) return
    
    if (isPlaying) {
      audioPlayerRef.current.pause()
    } else {
      audioPlayerRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  return (
    <div className="audio-recorder">
      {!isRecording && !audioURL ? (
        <button
          className="record-button start"
          onClick={startRecording}
          disabled={disabled}
        >
          <span className="mic-icon">🎤</span>
          <span>Start Recording</span>
        </button>
      ) : isRecording ? (
        <div className="recording-controls">
          <canvas 
            ref={canvasRef} 
            className="waveform-canvas"
            width="600"
            height="100"
          />
          <div className="recording-indicator">
            <div className="pulse-dot"></div>
            <span className="recording-time">{formatTime(recordingTime)}</span>
          </div>
          <button
            className="record-button stop"
            onClick={stopRecording}
          >
            <span className="stop-icon">⬛</span>
            <span>Stop Recording</span>
          </button>
        </div>
      ) : (
        <div className="playback-controls">
          <audio 
            ref={audioPlayerRef} 
            src={audioURL}
            onEnded={() => setIsPlaying(false)}
          />
          <div className="audio-player">
            <button 
              className="play-button"
              onClick={togglePlayPause}
            >
              {isPlaying ? '⏸️' : '▶️'}
            </button>
            <span className="player-label">
              {isPlaying ? 'Playing...' : 'Ready to submit'}
            </span>
          </div>
          <div className="action-buttons">
            <button
              className="record-button rerecord"
              onClick={handleReRecord}
            >
              <span>🔄 Re-record</span>
            </button>
            <button
              className="record-button submit"
              onClick={handleSubmitRecording}
            >
              <span>✓ Submit Recording</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AudioRecorder
