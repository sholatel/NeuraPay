import { useCallback, useEffect, useRef, useState } from 'react'
import { processVoiceOperation, AiApiError } from '../lib/ai-api'
import { useAuth } from '../providers/auth-context'

export type VoiceStatus =
  | 'idle'
  | 'requesting'
  | 'recording'
  | 'processing'
  | 'done'
  | 'error'

export interface VoiceRecorderState {
  status: VoiceStatus
  transcript: string
  /** Agent's natural language response to the voice command */
  response: string
  /** Name of the specialist agent that handled the request */
  agentName: string
  error: string
  /** 0–1 amplitude level, updated ~60 fps while recording */
  audioLevel: number
}

export interface VoiceRecorderControls {
  start: () => Promise<void>
  stop: () => void
  reset: () => void
}

function getSupportedMimeType(): string {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
  ]
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) ?? ''
}

export function useVoiceRecorder(): VoiceRecorderState & VoiceRecorderControls {
  const { session } = useAuth()
  const [status, setStatus] = useState<VoiceStatus>('idle')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [agentName, setAgentName] = useState('')
  const [error, setError] = useState('')
  const [audioLevel, setAudioLevel] = useState(0)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const rafRef = useRef<number>(0)
  const mimeTypeRef = useRef('')

  const stopAudioLevel = useCallback(() => {
    cancelAnimationFrame(rafRef.current)
    setAudioLevel(0)
  }, [])

  const tickAudioLevel = useCallback(() => {
    const analyser = analyserRef.current
    if (!analyser) return
    const data = new Uint8Array(analyser.frequencyBinCount)
    analyser.getByteFrequencyData(data)
    const avg = data.reduce((sum, v) => sum + v, 0) / data.length
    setAudioLevel(avg / 255)
    rafRef.current = requestAnimationFrame(tickAudioLevel)
  }, [])

  const releaseStream = useCallback(() => {
    stopAudioLevel()
    audioCtxRef.current?.close()
    audioCtxRef.current = null
    analyserRef.current = null
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }, [stopAudioLevel])

  const start = useCallback(async () => {
    setStatus('requesting')
    setTranscript('')
    setResponse('')
    setAgentName('')
    setError('')

    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 },
      })
    } catch (err) {
      const name = (err as DOMException).name
      const msg =
        name === 'NotAllowedError' || name === 'PermissionDeniedError'
          ? 'Microphone access denied. Please allow microphone access in your browser settings.'
          : 'Could not access your microphone. Please check your device.'
      setError(msg)
      setStatus('error')
      return
    }

    streamRef.current = stream

    // Wire up audio level analyser
    const ctx = new AudioContext()
    audioCtxRef.current = ctx
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 256
    analyserRef.current = analyser
    ctx.createMediaStreamSource(stream).connect(analyser)

    // Set up MediaRecorder
    const mimeType = getSupportedMimeType()
    mimeTypeRef.current = mimeType
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    recorderRef.current = recorder
    chunksRef.current = []

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.onstop = async () => {
      releaseStream()
      setStatus('processing')

      const blob = new Blob(chunksRef.current, {
        type: mimeTypeRef.current || 'audio/webm',
      })
      const ext = mimeTypeRef.current.includes('mp4') ? 'mp4' : 'webm'
      const token = session?.accessToken ?? ''

      try {
        const result = await processVoiceOperation(blob, `recording.${ext}`, token)
        setTranscript(result.transcript)
        setResponse(result.response)
        setAgentName(result.agent)
        setStatus('done')
      } catch (err) {
        const msg =
          err instanceof AiApiError
            ? err.message
            : 'Voice command failed. Please try again.'
        setError(msg)
        setStatus('error')
      }
    }

    recorder.start(100) // collect audio chunks every 100 ms
    setStatus('recording')
    rafRef.current = requestAnimationFrame(tickAudioLevel)
  }, [releaseStream, tickAudioLevel, session])

  const stop = useCallback(() => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
    }
  }, [])

  const reset = useCallback(() => {
    stop()
    releaseStream()
    setStatus('idle')
    setTranscript('')
    setResponse('')
    setAgentName('')
    setError('')
  }, [stop, releaseStream])

  // Clean up everything on unmount
  useEffect(() => () => { reset() }, [reset])

  return { status, transcript, response, agentName, error, audioLevel, start, stop, reset }
}
