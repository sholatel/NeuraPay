const AI_BASE = (import.meta.env.VITE_AI_SERVICE_URL as string | undefined) ?? 'http://localhost:8000'

export class AiApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message)
    this.name = 'AiApiError'
  }
}

export interface VoiceOperationResult {
  transcript: string
  response: string
  agent: string
}

export async function processVoiceOperation(
  blob: Blob,
  filename: string,
  token: string,
): Promise<VoiceOperationResult> {
  const form = new FormData()
  form.append('file', blob, filename)

  const res = await fetch(`${AI_BASE}/api/v1/operations/process-voice-operation`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { error?: string }
    throw new AiApiError(body.error ?? `Voice operation failed (HTTP ${res.status})`, res.status)
  }

  const body = await res.json() as { data?: VoiceOperationResult }
  return {
    transcript: body.data?.transcript ?? '',
    response: body.data?.response ?? '',
    agent: body.data?.agent ?? '',
  }
}
