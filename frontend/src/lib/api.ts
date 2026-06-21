import type {
  DepositPayload,
  LoginResponse,
  PaginatedResult,
  RegisterResponse,
  TransactionRecord,
  TransferPayload,
  WalletBalanceResponse,
  WalletSummary,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:3000/api'

export class ApiError extends Error {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }

    const data = (await response.json().catch(() => null)) as
      | { message?: string | string[] }
      | null

    const message = Array.isArray(data?.message)
      ? data.message.join(', ')
      : data?.message ?? 'Request failed'

    throw new ApiError(message, response.status)
  }

  return (await response.json()) as T
}

export function registerUser(payload: { name: string; email: string; password: string }) {
  return request<RegisterResponse>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function loginUser(payload: { email: string; password: string }) {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getWallets(token: string) {
  return request<WalletSummary[]>('/wallet', undefined, token)
}

export function getWalletBalance(token: string, userId: string, currency: string) {
  const search = new URLSearchParams({
    currency,
  })

  return request<WalletBalanceResponse>(
    `/wallet/${userId}/balance?${search.toString()}`,
    undefined,
    token,
  )
}

export function depositFunds(token: string, payload: DepositPayload) {
  return request('/wallet/deposit', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, token)
}

export function transferFunds(token: string, payload: TransferPayload) {
  return request('/wallet/transfer', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, token)
}

export function getTransactionHistory(
  token: string,
  params: { userId: string; currency: string; page: number; limit: number },
) {
  const safePage = Number.isInteger(params.page) && params.page > 0 ? params.page : 1
  const safeLimit =
    Number.isInteger(params.limit) && params.limit >= 1 && params.limit <= 100
      ? params.limit
      : 20

  const search = new URLSearchParams({
    currency: params.currency,
    page: String(safePage),
    limit: String(safeLimit),
  })

  return request<PaginatedResult<TransactionRecord>>(
    `/wallet/${params.userId}/transactions?${search.toString()}`,
    undefined,
    token,
  )
}