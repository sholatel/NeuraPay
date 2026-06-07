import type { VoiceStatus } from '../../hooks/use-voice-recorder'

interface VoiceButtonProps {
  status: VoiceStatus
  audioLevel: number
  onPress: () => void
}

const RING_DELAYS = ['0ms', '350ms', '700ms']

export function VoiceButton({ status, audioLevel, onPress }: VoiceButtonProps) {
  const isDisabled = status === 'requesting' || status === 'processing'

  // Scale the outer ring slightly with audio level so it "breathes" with the voice
  const dynamicScale = 1 + audioLevel * 0.3

  return (
    <div className="relative flex items-center justify-center" style={{ width: 88, height: 88 }}>

      {/* Ripple rings — visible only while recording */}
      {status === 'recording' &&
        RING_DELAYS.map((delay, i) => (
          <span
            key={i}
            className="absolute inset-0 rounded-full bg-slate-800/20"
            style={{
              animation: `voice-ring 1.5s ease-out ${delay} infinite`,
              transform: `scale(${dynamicScale})`,
            }}
          />
        ))}

      {/* Spinner ring — visible while processing */}
      {status === 'processing' && (
        <span className="absolute inset-0 rounded-full border-2 border-slate-200 border-t-teal-500 animate-spin" />
      )}

      {/* The button itself */}
      <button
        type="button"
        onClick={onPress}
        disabled={isDisabled}
        aria-label={
          status === 'recording' ? 'Stop recording' :
          status === 'processing' ? 'Processing…' :
          'Start voice recording'
        }
        className={[
          'relative z-10 flex items-center justify-center rounded-full transition-all duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2',
          'active:scale-95',
          isDisabled && 'cursor-not-allowed',
          buttonStyle(status),
        ].filter(Boolean).join(' ')}
        style={{ width: 72, height: 72 }}
      >
        <ButtonIcon status={status} />
      </button>
    </div>
  )
}

function buttonStyle(status: VoiceStatus): string {
  switch (status) {
    case 'idle':
    case 'done':
      return 'bg-teal-600 hover:bg-teal-500 shadow-[0_8px_32px_-8px_rgba(20,184,166,0.7)]'
    case 'requesting':
      return 'bg-teal-600/60'
    case 'recording':
      return 'bg-slate-950 shadow-[0_8px_32px_-8px_rgba(15,23,42,0.6)]'
    case 'processing':
      return 'bg-slate-100'
    case 'error':
      return 'bg-rose-50 hover:bg-rose-100 border border-rose-200'
  }
}

function ButtonIcon({ status }: { status: VoiceStatus }) {
  if (status === 'processing') {
    return (
      <svg className="w-7 h-7 text-slate-400" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" />
      </svg>
    )
  }

  if (status === 'recording') {
    // Stop icon
    return (
      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
        <rect x="6" y="6" width="12" height="12" rx="2" />
      </svg>
    )
  }

  if (status === 'error') {
    return (
      <svg className="w-6 h-6 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
    )
  }

  // Idle / done / requesting — mic icon
  return (
    <svg
      className={['w-7 h-7', status === 'requesting' ? 'text-white/60' : 'text-white'].join(' ')}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="9" y="2" width="6" height="12" rx="3" fill="currentColor" stroke="none" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 10a7 7 0 0014 0M12 19v3M8 22h8" />
    </svg>
  )
}
