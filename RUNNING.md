# Running Wallet Ledger System

This file is the dedicated run guide for the repository.

Its purpose is to help someone start the project locally as quickly as possible without reading the full project documentation.

The main project documentation is in `README.md`. That file covers the broader system architecture, design decisions, assumptions, and scaling approach. This file focuses only on running the project.

The Docker setup in this file is for local development convenience. It is not meant to imply that the production database should run in Docker.

## What This Starts

The repository contains:

- `backend/`: NestJS + TypeScript + PostgreSQL API
- `frontend/`: React + TypeScript + Vite demo UI

For local development, you typically run:

- PostgreSQL
- the backend API
- the frontend app

## Prerequisites

Install:

- Node.js 22 or a compatible recent Node.js version
- npm
- Docker Desktop if you want to run the backend and a local development PostgreSQL instance with Docker

## Quick Start

From the repository root:

```bash
cd backend
copy .env.example .env
npm install
docker-compose --profile dev up --build
```

In a second terminal from the repository root:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Default local URLs:

- backend API: `http://localhost:3000/api`
- frontend app: `http://localhost:5173`
- PostgreSQL host port: `5433`

## Backend Run Guide

### Option 1: Run backend with Docker for local development

From the repository root:

```bash
cd backend
copy .env.example .env
npm install
docker-compose --profile dev up --build
```

This starts:

- PostgreSQL on host port `5433`
- the NestJS development container on host port `3000`

This option is intended for local development and environment isolation. In production, the database should be managed separately and should not depend on this Docker Compose setup.

Alternative backend container profile:

```bash
cd backend
docker-compose --profile prod up --build
```

This only changes how the application container is started locally. It does not change the recommendation that production PostgreSQL should be managed outside Docker.

### Option 2: Run backend without Docker

First, make sure PostgreSQL is already running and that the database named in `DB_NAME` exists.

Then from the repository root:

```bash
cd backend
copy .env.example .env
npm install
npm run migration:run
npm run start:dev
```

Important backend environment values:

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

## Frontend Run Guide

From the repository root:

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Default frontend API target:

```bash
VITE_API_BASE_URL=http://localhost:3000/api
```

The frontend runs by default on:

- `http://localhost:5173`

## Typical Local Flow

1. Start the backend and database.
2. Start the frontend.
3. Open `http://localhost:5173`.
4. Register a user.
5. Log in.
6. Deposit funds.
7. Transfer funds.
8. Check the updated balance and transaction history.

## Known Local Note

If you change `DB_NAME` in `backend/.env` after PostgreSQL has already initialized the Docker volume, Postgres will not automatically create the new database inside the existing volume.

In that case:

1. create the database manually in the running container, or
2. reset the volume with `docker compose down -v` and start again

## Useful Commands

Backend:

```bash
cd backend
npm run build
npm run test
npm run test:e2e
npm run migration:run
```

Frontend:

```bash
cd frontend
npm run build
```