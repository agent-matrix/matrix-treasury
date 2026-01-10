# API Overview

## Base URL

```
Production:  https://api.matrix-treasury.io/api/v1
Staging:     https://staging-api.matrix-treasury.io/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### JWT Tokens

Most endpoints require JWT authentication:

```bash
curl -H "Authorization: Bearer <token>" \
     https://api.matrix-treasury.io/api/v1/metrics
```

### API Keys (Guardians Only)

Guardian services use API keys:

```bash
curl -H "X-API-Key: <guardian_key>" \
     -X POST https://api.matrix-treasury.io/api/v1/billing/charge \
     -d '{"agent_id": "agent_123", "metering": {...}}'
```

### Obtaining Tokens

```bash
# Login endpoint (returns JWT)
POST /api/v1/auth/login
{
    "username": "user@example.com",
    "password": "secret"
}

# Response
{
    "access_token": "eyJ0eXAiOiJKV1...",
    "refresh_token": "eyJ0eXAiOiJKV1...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

## Request Format

### Headers

```http
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <uuid>  # Optional, for tracing
```

### Body

JSON format, validated against Pydantic schemas:

```json
{
    "agent_id": "agent_123",
    "amount_mxu": 100.0
}
```

## Response Format

### Success Response

```json
{
    "status": "success",
    "data": {
        "balance": 1000.0,
        "agent_id": "agent_123"
    },
    "timestamp": "2024-01-10T12:00:00Z"
}
```

### Error Response

```json
{
    "error": {
        "code": "INSUFFICIENT_FUNDS",
        "message": "Agent has 50 MXU, needs 100 MXU",
        "details": {
            "required": 100.0,
            "available": 50.0
        }
    },
    "timestamp": "2024-01-10T12:00:00Z"
}
```

## Rate Limiting

Limits are per API key/user:

| Endpoint Type | Rate Limit |
|---------------|------------|
| Public (metrics) | 100/minute |
| Authenticated | 1000/minute |
| Write operations | 100/minute |
| Guardian metering | 10000/minute |

Headers returned:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1610280000
```

When exceeded:

```http
HTTP 429 Too Many Requests
Retry-After: 60
```

## Pagination

List endpoints support pagination:

```bash
GET /api/v1/transactions?page=1&page_size=50
```

Response:

```json
{
    "data": [...],
    "pagination": {
        "page": 1,
        "page_size": 50,
        "total_items": 1500,
        "total_pages": 30,
        "has_next": true,
        "has_previous": false
    }
}
```

## Idempotency

Write operations support idempotency keys:

```bash
POST /api/v1/transactions
Idempotency-Key: <uuid>

# Same request again returns cached response
```

## Versioning

API version is in the URL path: `/api/v1/`

Breaking changes will increment major version: `/api/v2/`

Non-breaking changes (additions) do not require version bump.

## OpenAPI Specification

Interactive documentation available at:

```
/docs       - Swagger UI
/redoc      - ReDoc
/openapi.json - OpenAPI 3.0 spec
```

## SDKs

Official SDKs:

- **Python**: `pip install matrix-treasury-sdk`
- **JavaScript**: `npm install @matrix/treasury-sdk`
- **Go**: `go get github.com/agent-matrix/treasury-go`

## Support

- **Issues**: https://github.com/agent-matrix/matrix-treasury/issues
- **Discord**: https://discord.gg/agent-matrix
- **Email**: api-support@agent-matrix.io
