import { useVoiceRecorder } from '../../hooks/use-voice-recorder'
import { VoiceButton } from './voice-button'

const BAR_DELAYS = ['0ms', '150ms', '300ms', '150ms', '0ms']

export function VoicePanel() {
  const { status, transcript, response, agentName, error, audioLevel, start, stop, reset } = useVoiceRecorder()

  function handleButtonPress() {
    if (status === 'idle' || status === 'done' || status === 'error') {
      void start()
    } else if (status === 'recording') {
      stop()
    }
  }

  return (
    <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            {status === 'recording' && (
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-rose-500" />
              </span>
            )}
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
              Voice Command
            </p>
          </div>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-950">
            {headerText(status)}
          </h2>
        </div>

        {(status === 'done' || status === 'error') && (
          <button
            type="button"
            onClick={reset}
            aria-label="Dismiss"
            className="rounded-full p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Button + visual feedback */}
      <div className="mt-6 flex flex-col items-center gap-4">
        <VoiceButton status={status} audioLevel={audioLevel} onPress={handleButtonPress} />

        {/* Waveform bars — recording only */}
        {status === 'recording' && (
          <div className="flex items-end gap-1" style={{ height: 24 }}>
            {BAR_DELAYS.map((delay, i) => (
              <span
                key={i}
                className="w-1.5 rounded-full bg-slate-800 origin-bottom"
                style={{
                  height: `${12 + audioLevel * 12}px`,
                  animation: `voice-bar ${0.6 + i * 0.08}s ease-in-out ${delay} infinite`,
                }}
              />
            ))}
          </div>
        )}

        {/* Status label */}
        <p className="text-sm font-medium text-slate-500">
          {statusLabel(status)}
        </p>
      </div>

      {/* Error message */}
      {status === 'error' && error && (
        <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* Result — transcript + agent response */}
      {status === 'done' && (
        <div className="mt-5 space-y-3">
          {transcript && (
            <div className="relative rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
              <span className="absolute -top-3 left-4 rounded-full bg-slate-600 px-2 py-0.5 text-xs font-semibold text-white">
                Heard
              </span>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">
                "{transcript}"
              </p>
            </div>
          )}

          {response && (
            <div className="relative rounded-2xl border border-teal-200 bg-teal-50 px-4 py-4">
              <span className="absolute -top-3 left-4 rounded-full bg-teal-600 px-2 py-0.5 text-xs font-semibold text-white">
                {agentName ? agentName.replace('_', ' ') : 'AI'}
              </span>
              <p className="mt-1 text-base leading-relaxed text-slate-800">
                {response}
              </p>
            </div>
          )}

          <button
            type="button"
            onClick={reset}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-950"
          >
            Record another command
          </button>
        </div>
      )}

      {/* Idle hint */}
      {status === 'idle' && (
        <p className="mt-5 text-center text-sm leading-6 text-slate-500">
          Try saying{' '}
          <span className="font-medium text-slate-700">"Send ₦5,000 to John"</span>
          {' '}or{' '}
          <span className="font-medium text-slate-700">"What's my balance?"</span>
        </p>
      )}
    </article>
  )
}

function headerText(status: ReturnType<typeof useVoiceRecorder>['status']): string {
  switch (status) {
    case 'idle':       return 'Speak to your wallet'
    case 'requesting': return 'Requesting microphone…'
    case 'recording':  return 'Listening…'
    case 'processing': return 'AI is thinking…'
    case 'done':       return 'Done'
    case 'error':      return 'Something went wrong'
  }
}

function statusLabel(status: ReturnType<typeof useVoiceRecorder>['status']): string {
  switch (status) {
    case 'idle':       return 'Tap to speak'
    case 'requesting': return 'Waiting for permission…'
    case 'recording':  return 'Tap to stop'
    case 'processing': return 'Transcribing and processing…'
    case 'done':       return 'Tap to record again'
    case 'error':      return 'Tap to try again'
  }
}
