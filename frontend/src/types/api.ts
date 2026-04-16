export type UserStatus = 'opened' | 'blocked' | 'onboarding'

export interface AuthUser {
  id: string
  name: string
  email: string
  status: UserStatus
}

export interface RegisterResponse {
  user: AuthUser & {
    createdAt: string
  }
  defaultWallet: {
    id: string
    userId: string
    currency: string
    createdAt: string
  }
}

export interface LoginResponse {
  accessToken: string
  user: AuthUser
}

export interface WalletSummary {
  id: string
  userId: string
  currency: string
  createdAt: string
  balance: number
}

export interface WalletBalanceResponse {
  walletId: string
  currency: string
  balance: number
}

export interface DepositPayload {
  amount: number
  currency: string
  reference: string
}

export interface TransferPayload extends DepositPayload {
  toUserId: string
}

export interface TransactionRecord {
  id: string
  walletId: string
  transactionId: string
  reference: string
  amount: number
  signedAmount: number
  currency: string
  direction: 'incoming' | 'outgoing'
  type: 'deposit' | 'transfer'
  status: 'pending' | 'success' | 'failed'
  counterpartyUserId: string | null
  createdAt: string
}

export interface PaginatedResult<T> {
  data: T[]
  meta: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

export interface SessionState {
  accessToken: string
  user: AuthUser
}