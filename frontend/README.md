# Engineering Report Evaluation — Frontend

A React SPA for the AI multi-agent engineering-report evaluation pipeline.

## Prerequisites

- Node.js 18+
- The backend must be running on **http://localhost:8000** (Vite will proxy `/api` → `:8000` automatically in dev).

## Getting started

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Build for production

```bash
npm run build
# output goes to dist/
npm run preview   # serve the production build locally
```

## Environment variables

Copy `.env.example` to `.env` and set `VITE_API_BASE` if your backend is
hosted at a different URL in production. Leave it empty in development.
