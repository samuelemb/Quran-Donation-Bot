# Quran Donation Bot

Production-ready v1 backend for a Telegram donation bot plus a shared FastAPI backend that a future admin portal can use.

## Stack

- Python 3.12+
- python-telegram-bot
- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Alembic
- APScheduler-ready jobs boundary
- pytest

## What is included

- Telegram donor bot
- Shared service layer for bot and portal/backend
- FastAPI admin-facing routes
- PostgreSQL models and Alembic migration
- Payment-method seed script
- Notification hooks for approval/rejection and subscription reminders
- Dockerfile and docker-compose
- Health/readiness endpoints
- Automated tests for services, API, and bot flows

## Donation flows

### New donor flow

1. User starts the bot and chooses a language.
2. User selects a donation plan: one-time, monthly, or 3-month.
3. User enters how many Qurans they want to donate.
4. User selects a payment method.
5. The bot shows the payment amount and account details.
6. User sends a payment screenshot.
7. The donation is stored as `pending` until an admin approves or rejects it.

### Returning subscription donor flow

1. After a monthly or 3-month donation is approved, the bot stores a subscription with the donor's saved Quran amount and payment method.
2. The scheduler sends reminder messages before the next payment due date.
3. Each reminder includes a `Donate Now` button.
4. When the donor taps `Donate Now`, the bot shows the saved amount and saved payment method, then asks for a fresh payment screenshot.
5. The new payment is submitted for review as another pending donation.

## Environment

Copy `.env.example` to `.env` and fill in real values.

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/quran_donation_bot
CHANNEL_LINK=https://t.me/your_channel
SUPPORT_CONTACT=@your_support_contact
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
ADMIN_API_KEY=change-me
ENABLE_SCHEDULER=false
```

## Install and run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m quran_donation_bot.app.scripts.seed_payment_methods
python run.py
```

Run API:

```bash
python run_api.py
```

## Docker

```bash
docker compose up --build
```

Services:

- Bot process: `python run.py`
- API process: `python run_api.py`
- Postgres: `localhost:5432`
- API health: `GET http://localhost:8000/health`

## API routes

- `GET /health`
- `GET /ready`
- `GET /api/v1/donations/pending`
- `GET /api/v1/donations/{id}`
- `PATCH /api/v1/donations/{id}/approve`
- `PATCH /api/v1/donations/{id}/reject`
- `GET /api/v1/users`
- `GET /api/v1/users/{id}`
- `GET /api/v1/payment-methods`
- `POST /api/v1/payment-methods`
- `PATCH /api/v1/payment-methods/{id}`
- `GET /api/v1/feedback`

Admin routes require header:

```text
X-Admin-Api-Key: <ADMIN_API_KEY>
```

## Seed payment methods

```bash
python -m quran_donation_bot.app.scripts.seed_payment_methods
```

## Approval flow example

1. User submits donation screenshot in Telegram.
2. Donation is stored with `pending` status and payment snapshot fields.
3. If the donation plan is recurring and the donation is approved, the backend creates or updates a subscription record for future reminders.
4. Admin portal or backend calls:

```http
PATCH /api/v1/donations/1/approve
X-Admin-Api-Key: change-me
Content-Type: application/json

{
  "reviewed_by": "admin@example.com",
  "review_notes": "Verified against payment record"
}
```

5. The backend updates the donation and sends the Telegram approval message.
6. For recurring plans, later reminder messages include a `Donate Now` button that takes the donor straight to the saved payment instructions and screenshot step.

## Tests

Run:

```bash
pytest
```

Coverage focus:

- donation calculation and creation
- approval/rejection workflow
- payment-method CRUD basics
- user settings updates
- FastAPI health and pending-donations routes
- Telegram donation and feedback conversation flows
