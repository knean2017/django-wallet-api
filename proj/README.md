# Transactional System Core

A fault-tolerant transaction API built with Django, DRF, Celery, Redis, and PostgreSQL.

## Features

- **Wallet & Transaction Models** - UUID-based wallets with balance tracking
- **Transfer API** - `POST /api/transfer/` with atomic transactions
- **Race Condition Protection** - Uses `select_for_update()` to prevent double spending
- **System Commission** - 10% fee on transfers > 1000 units, credited to admin wallet
- **Async Notifications** - Celery tasks with retry logic (3 retries, 3 sec delay)

## Quick Start with Docker

```bash
# Start all services
docker-compose up --build

# Run migrations (in another terminal)
docker-compose exec web python manage.py migrate

# Create test wallets
docker-compose exec web python manage.py shell
>>> from finance.models import Wallet
>>> Wallet.objects.create(owner="alice", balance=2000)
>>> Wallet.objects.create(owner="bob", balance=0)
```

## API Usage

### Transfer Funds

```bash
curl -X POST http://localhost:8000/api/transfer/ \
  -H "Content-Type: application/json" \
  -d '{
    "sender_wallet_id": "<alice-uuid>",
    "receiver_wallet_id": "<bob-uuid>",
    "amount": "1500.00"
  }'
```

**Response:**
```json
{
  "id": "...",
  "sender_wallet": "...",
  "receiver_wallet": "...",
  "amount": "1500.00",
  "commission_amount": "150.00",
  "currency": "USD",
  "created_at": "..."
}
```

## Running Tests

```bash
# With Docker
docker-compose exec web python manage.py test finance

# Local (with SQLite)
python manage.py test finance
```

## Race Condition Protection

The transfer service uses PostgreSQL's `SELECT FOR UPDATE` to lock wallet rows during transactions:

```python
locked_wallets = Wallet.objects.select_for_update().filter(
    id__in=[sender_id, receiver_id]
).order_by('id')  # Consistent ordering prevents deadlocks
```

This ensures that concurrent requests cannot cause double spending.

## Project Structure

```
proj/
├── finance/
│   ├── models.py      # Wallet, Transaction models
│   ├── services.py    # TransferService with atomic transfers
│   ├── views.py       # TransferView API endpoint
│   ├── tasks.py       # Celery notification task
│   ├── signals.py     # Auto-create admin wallet
│   └── tests.py       # API tests
├── proj/
│   ├── settings.py    # Django settings
│   └── celery.py      # Celery configuration
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
