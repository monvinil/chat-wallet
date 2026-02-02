# USDChat Quick Start Guide

## Development Setup

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker (optional, for containerized development)

### Option 1: Run Locally (Recommended for Development)

**1. Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

**2. Start the FastAPI backend:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run API server
python run_api.py --debug
```
API will be available at `http://localhost:8000`

**3. Start the Next.js frontend:**
```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```
Frontend will be available at `http://localhost:3000`

**4. (Optional) Start the scheduler worker:**
```bash
# In a separate terminal
python scheduler_executor.py --mode worker --interval 60
```

### Option 2: Run with Docker Compose

```bash
# Start API and frontend
docker-compose up

# Or with scheduler worker
docker-compose --profile with-scheduler up
```

---

## Project Structure

```
chat-wallet/
├── api/                    # FastAPI backend
│   ├── routes/             # API endpoints
│   │   ├── wallet.py       # Wallet CRUD
│   │   ├── transactions.py # Send/receive
│   │   ├── yield_routes.py # Aave yield
│   │   ├── scheduler_routes.py # DCA
│   │   └── earnings_routes.py  # Earnings
│   ├── schemas/            # Pydantic models
│   └── middleware/         # Auth, rate limiting
├── web/                    # Next.js frontend
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── lib/                # API client, stores, hooks
│   └── public/             # Static assets
├── sdk/                    # Agent SDK (Phase 3)
├── migrations/             # Database migrations
└── docs/                   # Documentation
```

---

## Available Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wallet/create` | POST | Create wallet |
| `/api/v1/wallet/login` | POST | Login |
| `/api/v1/wallet/refresh` | POST | Refresh token |

### Wallet
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wallet/balance` | GET | Get balances |
| `/api/v1/wallet/address/{chain}` | GET | Get deposit address |

### Transactions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/transactions/preview` | POST | Preview transaction |
| `/api/v1/transactions/send` | POST | Send transaction |
| `/api/v1/transactions/history` | GET | Get history |

### Yield (Aave)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/yield/status` | GET | Get yield status |
| `/api/v1/yield/deposit` | POST | Deposit to Aave |
| `/api/v1/yield/withdraw` | POST | Withdraw from Aave |

### Scheduler (DCA)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scheduler/create` | POST | Create DCA schedule |
| `/api/v1/scheduler/list` | GET | List schedules |
| `/api/v1/scheduler/{id}/pause` | POST | Pause schedule |
| `/api/v1/scheduler/{id}/resume` | POST | Resume schedule |
| `/api/v1/scheduler/{id}/cancel` | POST | Cancel schedule |

### Earnings
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/earnings/summary` | GET | Get earnings summary |
| `/api/v1/earnings/history` | GET | Get earnings history |

---

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/` | Redirect to login or wallet |
| `/login` | Login page |
| `/signup` | Create wallet page |
| `/wallet` | Dashboard with balances |
| `/earn` | Yield + DCA management |
| `/send` | Send USDC |
| `/receive` | Receive with QR code |
| `/history` | Transaction history |

---

## Testing

**Backend:**
```bash
# Run API tests
pytest tests/

# Run with coverage
pytest --cov=api tests/
```

**Frontend:**
```bash
cd web

# Type check
npm run build

# Lint
npm run lint
```

---

## Deployment

### Production Checklist
- [ ] Set `DEBUG=false` in API config
- [ ] Generate secure `JWT_SECRET_KEY`
- [ ] Configure production Supabase instance
- [ ] Set up RPC endpoints (Alchemy/Infura)
- [ ] Deploy scheduler worker separately
- [ ] Configure CORS origins for production domain

### Recommended Platforms
- **API:** Railway, Fly.io, or Render
- **Frontend:** Vercel (automatic Next.js optimization)
- **Scheduler:** Railway (background worker) or external cron

---

## Phase 1 Status: COMPLETE

- [x] Next.js scaffold with shadcn/ui
- [x] JWT authentication flow
- [x] Yield API (Aave integration)
- [x] Scheduler API (DCA)
- [x] Earnings API
- [x] All frontend pages

## Next: Phase 2 (PWA + Retention)

- [ ] Configure next-pwa
- [ ] Push notifications (Firebase/OneSignal)
- [ ] Email notifications (Resend/SendGrid)
- [ ] Mobile UI polish

---

*Last Updated: February 2026*
