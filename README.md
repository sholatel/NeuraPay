# Wallet Ledger System

Wallet Ledger System is a full-stack demo of a ledger-based fintech wallet platform.

The repository contains:

- `backend/`: NestJS + TypeScript + PostgreSQL API
- `frontend/`: React + TypeScript + Vite + Tailwind demo UI

This README is the top-level project document for the repository and answers the required documentation questions:

- system architecture
- key design decisions
- assumptions made
- how to run locally
- how the system would scale to 10 million transactions per day

If you only need startup and local execution steps, see `RUNNING.md`. That file is the dedicated run guide, while this README remains the main project documentation.

## Repository Structure

```text
wallet-ledger-system/
├── backend/
│   ├── src/
│   │   ├── common/
│   │   ├── db/
│   │   └── modules/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── docker-compose.yml
│   └── package.json
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── lib/
    │   ├── pages/
    │   ├── providers/
    │   └── types/
    └── package.json
```

## System Architecture

The system is split into two layers.

### Backend

The backend is a NestJS application structured around focused modules:

- `auth`: login and JWT issuance
- `user`: user creation and retrieval
- `wallet`: wallet queries, deposit, transfer, wallet-scoped balance and history endpoints
- `transaction`: transaction history assembly from ledger entries
- `ledger`: immutable balance source of truth
- `notification`: best-effort email notification dispatch
- `db`: TypeORM configuration and migrations
- `common`: guards, decorators, and utilities

The backend uses PostgreSQL and TypeORM. The ledger is the accounting source of truth. Deposits and transfers create immutable ledger rows, and balances are derived from the ledger rather than stored directly as an authoritative value.

### Frontend

The frontend is a React single-page application with:

- login page
- registration page
- protected dashboard
- wallet balance display
- account number display
- deposit form
- transfer form
- transaction history view

Authentication state is stored client-side and the frontend calls the backend using JWT-protected requests.

### Request/Data Flow

The high-level request flow is:

1. A user registers or logs in.
2. The backend returns a JWT.
3. The frontend stores the authenticated session.
4. The dashboard loads wallet data from the backend.
5. Deposits and transfers call backend wallet endpoints.
6. The backend writes transaction and ledger rows inside database transactions.
7. The frontend refreshes wallet balance and transaction history.

## Backend Domain Model

The important backend entities are:

- `users`: customer identity, account status, credentials
- `wallets`: wallet container per user and currency
- `transactions`: business event record for deposits and transfers
- `ledger_entries`: immutable debit and credit rows used to calculate balances

### Balance Model

Balances are computed from ledger entries:

```sql
SELECT COALESCE(SUM(amount), 0)
FROM ledger_entries
WHERE wallet_id = $1;
```

That means:

- no balance drift from stale cached columns
- easier auditability
- a full event trail for deposits and transfers

## API Shape

The API is served from the Nest global prefix:

- `http://localhost:3000/api`

Important routes in the current implementation include:

### Auth

- `POST /api/auth/login`

### Users

- `POST /api/users`
- `GET /api/users/:id`

### Wallet actions

- `POST /api/wallet/deposit`
- `POST /api/wallet/transfer`
- `GET /api/wallet`

### Wallet-scoped queries

- `GET /api/wallet/:userId/balance?currency=NGN`
- `GET /api/wallet/:userId/transactions?currency=NGN&page=1&limit=10`

If `currency` is omitted or blank for balance/history, the backend defaults to `NGN`.

## Key Design Decisions

### 1. NestJS for modular domain boundaries

I chose NestJS for this project because its modular architecture fits this problem well.

Why:

- the domain already breaks down naturally into auth, user, wallet, ledger, transaction, and notification concerns
- module boundaries make the codebase easier to reason about while the system is still a monolith
- a fintech system like this would likely evolve into microservices later
- NestJS makes it straightforward to isolate one module, or a related set of modules, into its own service when the system grows

### 2. Docker for backend environment consistency

I chose Docker for the backend development workflow so the API can be run in a predictable, repeatable environment and local dependencies can be isolated easily.

Why:

- it reduces local setup differences across machines
- it makes onboarding easier because the backend and a local development database can be started with a small number of commands
- it isolates development infrastructure cleanly during local work
- it lowers the risk of environment-specific issues around Node, PostgreSQL, ports, and dependencies
- it provides a cleaner path to later infrastructure automation for the application layer

This does not mean the production database should run in Docker. The containerized PostgreSQL setup is primarily a development convenience. In production, the database should be deployed and managed separately from the application containers so persistence, backups, failover, scaling, and operational controls can be handled with the right database-focused tooling.

### 3. Ledger as the source of truth

The most important design choice is using ledger entries instead of a writable balance column.

Why:

- balances remain derivable from immutable events
- auditing is simpler
- transfer correctness is easier to reason about
- later projections or caches can be built without losing the canonical history

### 4. Double-entry transfers

Transfers create:

- one debit entry on the sender wallet
- one credit entry on the receiver wallet
- one `transactions` row linking the business event

Why:

- preserves accounting symmetry
- keeps transfer effects traceable
- makes reconciliation easier

### 5. Database transactions around money movement

Deposits and transfers run inside database transactions.

Why:

- business event and ledger mutations succeed or fail together
- transfer partial writes are avoided

### 6. Row-level locking on transfer sender wallet

Transfers use pessimistic locking on the sender wallet row before balance verification and debit write.

Why:

- prevents concurrent overspending on the same sender wallet
- keeps locking narrower than locking unrelated rows

### 7. JWT-protected wallet access

Wallet and transaction endpoints are protected by JWT auth, and wallet-scoped balance/history routes enforce that a user can only query their own `userId`.

Why:

- keeps wallet data access tied to the authenticated principal
- prevents simple path-parameter based data leakage

### 8. Account status guard for transactions

Deposit and transfer actions are protected by an account-status guard.

Why:

- models a fintech-style lifecycle where account state matters
- keeps policy enforcement out of controller body logic

### 9. Best-effort notifications

Notification sending does not block the financial transaction from succeeding.

Why:

- notifications are side effects, not the financial source of truth
- users should not lose a successful transaction because SMTP failed

### 10. User ID as account number in the demo

The frontend currently displays the authenticated user ID as the account number.

Why:

- avoids inventing a fake numbering scheme before there is a real business rule for account numbering
- keeps the demo functional while still surfacing an account identifier in the UI

## Assumptions Made

The implementation makes the following assumptions:

- each new user gets a default `NGN` wallet at registration time
- the demo supports same-currency transfers only
- the platform is expected to evolve later to support broader multi-currency wallet and transaction flows
- `NGN` is the default currency when no currency is supplied for wallet balance or transaction history
- user email is required because login and notifications use it
- a password hash field is required even though the original brief focused on wallet behavior
- user status is part of the domain model to represent fintech-style account control
- the demo uses user ID as account number
- SMTP configuration is optional for local development; financial operations still succeed if email delivery fails
- the frontend is a demo client, not a full production-grade consumer application

## How To Run The Project Locally

## Prerequisites

Install:

- Node.js 22 or compatible recent Node.js version
- npm
- Docker Desktop or a local PostgreSQL instance

## 1. Backend setup

From the repository root:

```bash
cd backend
```

Install dependencies:

```bash
npm install
```

Create environment file:

```bash
copy .env.example .env
```

Important backend variables:

- `PORT`
- `DB_HOST`
- `DB_PORT`
- `DB_USERNAME`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`
- `JWT_EXPIRES_IN`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_FROM`

### Run backend with Docker

Development profile:

```bash
docker-compose --profile dev up --build
```

This starts:

- PostgreSQL on host port `5433`
- NestJS dev container on host port `3000`

Alternative backend container profile:

```bash
docker-compose --profile prod up --build
```

This starts:

- production-style Nest container on host port `3001`

This profile is still for running the application container locally. It should not be read as a recommendation to run the production database in Docker.

### Run backend without Docker

Start PostgreSQL yourself and make sure the database named in `DB_NAME` exists.

Then run:

```bash
npm run migration:run
npm run start:dev
```

Useful backend commands:

```bash
npm run build
npm run test
npm run test:e2e
npm run migration:run
```

## 2. Frontend setup

From the repository root:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Optional frontend environment file:

```bash
copy .env.example .env
```

Default frontend API target:

```bash
VITE_API_BASE_URL=http://localhost:3000/api
```

Start the frontend:

```bash
npm run dev
```

The frontend runs by default on:

- `http://localhost:5173`

Build the frontend:

```bash
npm run build
```

## 3. End-to-end local flow

Typical local development flow:

1. Start the backend and database.
2. Start the frontend.
3. Register a user.
4. Log in.
5. View the generated wallet and account number.
6. Deposit funds.
7. Transfer funds to another user.
8. Check balance and transaction history.

## Known Local Setup Note

If you change `DB_NAME` in `.env` after PostgreSQL has already initialized the named Docker volume, Postgres will not automatically create the new database inside the existing volume.

In that case, either:

1. create the database manually inside the running container, or
2. reset the volume with `docker compose down -v` and start again

## Scaling Question

If this system needed to process 10 million transactions per day, I would scale it across infrastructure, database design, asynchronous processing, caching, and observability.

### Infrastructure

I would run the backend as multiple stateless application instances behind a load balancer.

At that scale, I would also begin breaking the current monolith into focused microservices. A practical split for this codebase would be:

- `auth-service`: authentication, token issuance, credential validation, and auth-related policies
- `wallet-ledger-service`: user profile, wallet operations, transaction processing, and ledger writes
- `notification-service`: email and other future notification channels

This decomposition follows the current module boundaries closely, which is one of the reasons NestJS was a good fit for the project from the start.

Key changes:

- container orchestration with Kubernetes or a similar platform
- horizontal scaling of API workers
- progressive decomposition of the monolith into `auth-service`, `wallet-ledger-service`, and `notification-service`
- separate worker services for non-request-driven jobs
- environment separation for production, staging, and development
- autoscaling based on CPU, latency, queue depth, and database connection pressure

### Database Design

At 10 million transactions per day, PostgreSQL can still be part of the solution, but the schema and operational model must be tightened.

I would do the following:

- partition `ledger_entries` and likely `transactions` by time and possibly by tenant or wallet domain
- add carefully chosen indexes for high-volume query paths
- keep writes on the primary database and move reporting reads to replicas where appropriate
- reduce large-table scans by using targeted materialized views or balance projections
- tune connection pooling aggressively
- preserve immutable ledger writes and avoid balance mutation as the canonical source of truth

For balance lookups at that scale, I would likely introduce derived balance projections that are updated from the ledger while still keeping the ledger as the source of truth for reconciliation.

### Queues And Asynchronous Processing

High-volume systems should not perform every side effect inline with the user request.

I would introduce queues for:

- notifications
- webhooks
- reporting events
- audit export pipelines
- balance projection updates
- fraud/risk scoring side effects

The synchronous request path should remain focused on the smallest atomic unit necessary for financial correctness: transaction validation, transaction write, ledger write, and response.

### Caching

Caching should be selective and safe.

I would cache:

- wallet summaries
- read-heavy transaction history pages where appropriate
- user profile metadata
- permission/account status lookups

I would not treat cache as the financial source of truth. Cached balance values should be projections or read models that can always be rebuilt from the ledger.

### Monitoring And Observability

For a financial system, observability is not optional.

I would also introduce centralized logging with the ELK stack and separate log processing from the core transaction path.

At a higher scale, I would add a dedicated log service responsible for receiving operational log events, processing them, and storing the raw log stream in a NoSQL store. Elasticsearch would sit alongside that flow as the indexing and search layer that Kibana can query for fast operational investigations and dashboards. Application services would publish log events asynchronously so that logging remains reliable without slowing down the main request path.

I would prefer NoSQL for raw log storage because logs are high-volume, append-heavy, and often semi-structured. The schema can evolve frequently across services, and retention policies may differ by log class. A NoSQL store is a better fit for flexible ingestion, horizontal write scaling, and cheap retention than a relational transactional database. I would not use the primary relational database for this because it should stay focused on strongly consistent financial data, not operational log traffic.

I would add:

- structured logs with correlation IDs
- Elasticsearch and Kibana for fast search, filtering, and operational analysis of indexed logs
- a dedicated log service that ingests, normalizes, and persists raw logs in a NoSQL-backed logging store
- event-based log publishing so application services can emit logs to the logging pipeline asynchronously
- request tracing across API, database, and async workers
- metrics for transaction throughput, failure rates, queue lag, and DB latency
- dashboards for balance query latency and transfer success rate
- alerts for migration failures, deadlocks, connection exhaustion, unusual retry spikes, and queue backlog
- immutable audit logging for sensitive actions

### Operational Priorities At 10 Million Transactions Per Day

The first priorities would be:

1. preserve correctness of financial writes
2. isolate the write path from slow side effects
3. reduce database contention on hot wallets
4. partition and index ledger/history data properly
5. introduce balance projections for high-frequency reads
6. monitor aggressively and rehearse failure handling

## Summary

This project is intentionally built around a ledger-first backend because that is the most important architectural choice for correctness in a wallet system. The frontend demonstrates the primary user operations, while the backend structure keeps the accounting logic, access control, and transaction history flow separated into clear modules.
