import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import {
  ApiError,
  depositFunds,
  getWalletBalance,
  getTransactionHistory,
  getWallets,
  transferFunds,
} from '../lib/api'
import { buildReference, formatDate, formatMoney } from '../lib/format'
import { useAuth } from '../providers/auth-context'
import type { TransactionRecord, WalletSummary } from '../types/api'

const HISTORY_PAGE_SIZE = 10

export function DashboardPage() {
  const { session, logout } = useAuth()
  const [wallets, setWallets] = useState<WalletSummary[]>([])
  const [selectedCurrency, setSelectedCurrency] = useState('NGN')
  const [currentBalance, setCurrentBalance] = useState(0)
  const [history, setHistory] = useState<TransactionRecord[]>([])
  const [historyPage, setHistoryPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [depositAmount, setDepositAmount] = useState('')
  const [transferAmount, setTransferAmount] = useState('')
  const [recipientUserId, setRecipientUserId] = useState('')
  const [depositing, setDepositing] = useState(false)
  const [transferring, setTransferring] = useState(false)
  const hasLoadedWallets = useRef(false)

  const token = session?.accessToken ?? ''
  const userId = session?.user.id ?? ''

  const loadDashboard = useCallback(async (page: number, nextCurrency?: string, initialLoad = false) => {
    try {
      if (initialLoad) {
        setLoading(true)
      } else {
        setRefreshing(true)
      }

      setError('')
      const walletList = await getWallets(token)
      setWallets(walletList)

      const resolvedCurrency =
        walletList.find((wallet) => wallet.currency === (nextCurrency ?? selectedCurrency))?.currency ??
        walletList[0]?.currency ??
        'NGN'

      const safePage = Number.isInteger(page) && page > 0 ? page : 1

      const [balanceResponse, historyResponse] = await Promise.all([
        getWalletBalance(token, userId, resolvedCurrency),
        getTransactionHistory(token, {
          userId,
          currency: resolvedCurrency,
          page: safePage,
          limit: HISTORY_PAGE_SIZE,
        }),
      ])

      setSelectedCurrency(resolvedCurrency)
      setCurrentBalance(balanceResponse.balance)

      setHistory(historyResponse.data)
      setTotalPages(historyResponse.meta.totalPages)

      if (historyResponse.meta.page !== safePage) {
        setHistoryPage(historyResponse.meta.page)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load dashboard data')
      setHistory([])
      setTotalPages(1)
    }
    finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [selectedCurrency, token, userId])

  const refreshDashboard = useCallback(async () => {
    await loadDashboard(historyPage, selectedCurrency)
  }, [historyPage, loadDashboard, selectedCurrency])

  useEffect(() => {
    if (!token || hasLoadedWallets.current) {
      return
    }

    hasLoadedWallets.current = true
    void loadDashboard(1, selectedCurrency, true)
  }, [loadDashboard, selectedCurrency, token])

  useEffect(() => {
    if (!token || !selectedCurrency || !hasLoadedWallets.current) {
      return
    }

    void loadDashboard(historyPage, selectedCurrency)
  }, [historyPage, loadDashboard, selectedCurrency, token])

  async function handleDeposit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setDepositing(true)
    setError('')
    setNotice('')

    try {
      await depositFunds(token, {
        amount: Number(depositAmount),
        currency: selectedCurrency,
        reference: buildReference('DEP'),
      })

      setNotice('Deposit completed successfully.')
      setDepositAmount('')
      setHistoryPage(1)
      await loadDashboard(1, selectedCurrency)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Deposit failed')
    } finally {
      setDepositing(false)
    }
  }

  async function handleTransfer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setTransferring(true)
    setError('')
    setNotice('')

    try {
      await transferFunds(token, {
        toUserId: recipientUserId,
        amount: Number(transferAmount),
        currency: selectedCurrency,
        reference: buildReference('TRF'),
      })

      setNotice('Transfer completed successfully.')
      setTransferAmount('')
      setRecipientUserId('')
      setHistoryPage(1)
      await loadDashboard(1, selectedCurrency)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Transfer failed')
    } finally {
      setTransferring(false)
    }
  }

  if (!session) {
    return null
  }

  const selectedWallet = wallets.find((wallet) => wallet.currency === selectedCurrency)

  return (
    <main className="min-h-screen px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_24px_80px_-32px_rgba(15,23,42,0.35)] backdrop-blur">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
                Wallet Dashboard
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                {session.user.name}
              </h1>
              <p className="mt-2 text-sm text-slate-600">
                {session.user.email} · Status: <span className="font-medium capitalize">{session.user.status}</span>
              </p>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600">
                Your wallet is created during registration. Use the forms below to deposit funds, transfer to another user, and inspect transaction history from the ledger-backed API.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void refreshDashboard()}
                className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-950"
              >
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              <button
                type="button"
                onClick={logout}
                className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {notice ? (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {notice}
          </div>
        ) : null}

        <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
          <article className="rounded-[28px] border border-slate-200/70 bg-slate-950 p-6 text-white shadow-[0_20px_70px_-36px_rgba(15,23,42,0.7)]">
            <p className="text-sm uppercase tracking-[0.2em] text-teal-300">Current wallet balance</p>
            <div className="mt-6 flex items-end justify-between gap-4">
              <div>
                <p className="text-4xl font-semibold tracking-tight">
                  {formatMoney(currentBalance, selectedCurrency)}
                </p>
                <p className="mt-2 text-sm text-slate-300">
                  Wallet ID: {selectedWallet?.id ?? 'Not available'}
                </p>
              </div>
              <select
                value={selectedCurrency}
                onChange={(event) => {
                  setSelectedCurrency(event.target.value)
                  setHistoryPage(1)
                }}
                className="rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-white outline-none"
              >
                {wallets.length === 0 ? <option value="NGN">NGN</option> : null}
                {wallets.map((wallet) => (
                  <option key={wallet.id} value={wallet.currency} className="text-slate-900">
                    {wallet.currency}
                  </option>
                ))}
              </select>
            </div>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">
            <p className="text-sm font-medium text-slate-500">Account number</p>
            <p className="mt-3 break-all text-xl font-semibold text-slate-950">{session.user.id}</p>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              This demo uses the user ID as the account number.
            </p>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">
            <p className="text-sm font-medium text-slate-500">Wallets</p>
            <p className="mt-3 text-3xl font-semibold text-slate-950">{wallets.length}</p>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              This demo backend creates the default wallet during registration.
            </p>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">
            <p className="text-sm font-medium text-slate-500">Transactions</p>
            <p className="mt-3 text-3xl font-semibold text-slate-950">{history.length}</p>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Latest page for {selectedCurrency} with up to {HISTORY_PAGE_SIZE} items.
            </p>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.9fr_0.9fr_1.2fr]">
          <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">
            <h2 className="text-xl font-semibold text-slate-950">Deposit funds</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Credit your selected wallet. A unique reference is generated automatically.
            </p>

            <form className="mt-6 space-y-4" onSubmit={handleDeposit}>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Amount</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  required
                  value={depositAmount}
                  onChange={(event) => setDepositAmount(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-teal-500 focus:bg-white"
                  placeholder="1000"
                />
              </label>

              <button
                type="submit"
                disabled={depositing || loading}
                className="w-full rounded-2xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {depositing ? 'Processing deposit...' : `Deposit into ${selectedCurrency}`}
              </button>
            </form>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">
            <h2 className="text-xl font-semibold text-slate-950">Transfer funds</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Send money to another registered user using their user ID. A unique reference is generated automatically.
            </p>

            <form className="mt-6 space-y-4" onSubmit={handleTransfer}>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Recipient user ID</span>
                <input
                  type="text"
                  required
                  value={recipientUserId}
                  onChange={(event) => setRecipientUserId(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-teal-500 focus:bg-white"
                  placeholder="UUID of the recipient user"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Amount</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  required
                  value={transferAmount}
                  onChange={(event) => setTransferAmount(event.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-teal-500 focus:bg-white"
                  placeholder="500"
                />
              </label>

              <button
                type="submit"
                disabled={transferring || loading}
                className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {transferring ? 'Sending transfer...' : `Transfer from ${selectedCurrency}`}
              </button>
            </form>
          </article>

          <article className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-[0_20px_70px_-36px_rgba(15,23,42,0.35)] backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Transaction history</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Recent ledger activity for {selectedCurrency}.
                </p>
              </div>
              <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Page {historyPage} of {totalPages}
              </div>
            </div>

            {loading ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">
                Loading dashboard...
              </div>
            ) : history.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">
                No transactions yet for this wallet.
              </div>
            ) : (
              <div className="mt-6 space-y-3">
                {history.map((entry) => (
                  <div
                    key={entry.id}
                    className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${entry.direction === 'incoming' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}
                          >
                            {entry.direction}
                          </span>
                          <span className="text-sm font-medium capitalize text-slate-700">{entry.type}</span>
                        </div>
                        <p className="mt-3 text-sm text-slate-500">{formatDate(entry.createdAt)}</p>
                        {entry.counterpartyUserId ? (
                          <p className="mt-1 break-all text-sm text-slate-500">
                            Counterparty: {entry.counterpartyUserId}
                          </p>
                        ) : null}
                      </div>

                      <div className="text-left sm:text-right">
                        <p
                          className={`text-lg font-semibold ${entry.direction === 'incoming' ? 'text-emerald-700' : 'text-slate-950'}`}
                        >
                          {entry.direction === 'incoming' ? '+' : '-'}
                          {formatMoney(entry.amount, entry.currency)}
                        </p>
                        <p className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
                          {entry.status}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setHistoryPage((page) => Math.max(page - 1, 1))}
                disabled={historyPage === 1}
                className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setHistoryPage((page) => Math.min(page + 1, totalPages))}
                disabled={historyPage >= totalPages}
                className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </article>
        </section>
      </div>
    </main>
  )
}