import React, { useState, useRef } from 'react'
import './AudioRecorder.css'

const AudioRecorder = ({ onRecordingComplete, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)

  const startRecording = async () => {
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
        onRecordingComplete(file)
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
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

  return (
    <div className="audio-recorder">
      {!isRecording ? (
        <button
          className="record-button start"
          onClick={startRecording}
          disabled={disabled}
        >
          <span className="mic-icon">🎤</span>
          <span>Start Recording</span>
        </button>
      ) : (
        <div className="recording-controls">
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
      )}
    </div>
  )
}

export default AudioRecorder
