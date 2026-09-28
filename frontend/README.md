# Blast Ecom frontend

The React + TypeScript + Vite application is scaffolded. The only current screen is a Spanish placeholder that explicitly says checkout is not available yet.

Use Node.js 24.21.0 (`.nvmrc`) and npm. From this directory:

```bash
npm ci
npm run dev
npm run typecheck
npm test
npm run lint
npm run format:check
npm run build
```

The development server proxies `/api`, `/admin` and `/static` to Django at `127.0.0.1:8000`. The backend and PostgreSQL must be running for proxied routes; the complete local setup is documented in [`docs/development/local-development.md`](../docs/development/local-development.md).
