import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export function AuthShell({
  title,
  subtitle,
  footer,
  children,
}: {
  title: string
  subtitle: string
  footer: ReactNode
  children: ReactNode
}) {
  return (
    <main className="min-h-screen px-4 py-10 text-slate-900">
      <div className="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[28px] border border-white/70 bg-white/80 p-8 shadow-[0_24px_80px_-32px_rgba(15,23,42,0.35)] backdrop-blur lg:p-10">
          <div className="mb-8 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
                Wallet Ledger Demo
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                {title}
              </h1>
              <p className="mt-3 max-w-md text-sm leading-6 text-slate-600">{subtitle}</p>
            </div>
            <Link
              to="/"
              className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
            >
              Home
            </Link>
          </div>
          {children}
          <div className="mt-6 text-sm text-slate-600">{footer}</div>
        </section>

        <aside className="rounded-[28px] bg-slate-950 p-8 text-white shadow-[0_24px_80px_-32px_rgba(15,23,42,0.55)] lg:p-10">
          <div>
            <p className="text-sm uppercase tracking-[0.22em] text-teal-300">What this demo covers</p>
            <ul className="mt-6 space-y-4 text-sm leading-6 text-slate-300">
              <li>Register a user and open the default NGN wallet.</li>
              <li>Login with JWT-backed authentication.</li>
              <li>Check balances, deposit funds, and transfer to another user.</li>
              <li>Review transaction history from the ledger-backed backend.</li>
            </ul>
          </div>
        </aside>
      </div>
    </main>
  )
}