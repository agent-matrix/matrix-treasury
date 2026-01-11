# Error Handling

Comprehensive guide to error handling in Matrix Treasury API.

## Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "UNIQUE_ERROR_CODE",
  "status_code": 400,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/agents/onboard",
  "request_id": "req_abc123"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Human-readable error description |
| `error_code` | string | Machine-readable error code |
| `status_code` | number | HTTP status code |
| `timestamp` | string | ISO 8601 timestamp |
| `path` | string | Request path that caused error |
| `request_id` | string | Unique request identifier for tracking |

## HTTP Status Codes

### 2xx Success

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE (no response body) |

### 4xx Client Errors

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid input, malformed JSON |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists, state conflict |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Meaning | Action |
|------|---------|--------|
| 500 | Internal Server Error | Server-side bug, contact support |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Temporary outage, retry later |
| 504 | Gateway Timeout | Request timeout, retry with backoff |

## Error Codes

### Authentication Errors

| Code | Status | Description |
|------|--------|-------------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Username or password incorrect |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT token has expired |
| `AUTH_TOKEN_INVALID` | 401 | JWT token malformed or invalid |
| `AUTH_TOKEN_MISSING` | 401 | Authorization header missing |
| `AUTH_INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `AUTH_ACCOUNT_DISABLED` | 403 | Admin account is disabled |

**Example**:
```json
{
  "detail": "JWT token has expired. Please login again.",
  "error_code": "AUTH_TOKEN_EXPIRED",
  "status_code": 401,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/analytics/vitals"
}
```

### Validation Errors

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_FAILED` | 422 | Request validation failed |
| `VALIDATION_MISSING_FIELD` | 422 | Required field missing |
| `VALIDATION_INVALID_FORMAT` | 422 | Field format invalid |
| `VALIDATION_OUT_OF_RANGE` | 422 | Value out of acceptable range |
| `VALIDATION_INVALID_CURRENCY` | 422 | Unsupported currency |
| `VALIDATION_INVALID_NETWORK` | 422 | Unsupported blockchain network |

**Example**:
```json
{
  "detail": "Validation failed for field 'amount': must be positive",
  "error_code": "VALIDATION_OUT_OF_RANGE",
  "status_code": 422,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/treasury/deposit",
  "validation_errors": {
    "amount": ["Value must be greater than 0"]
  }
}
```

### Agent Errors

| Code | Status | Description |
|------|--------|-------------|
| `AGENT_NOT_FOUND` | 404 | Agent ID doesn't exist |
| `AGENT_ALREADY_EXISTS` | 409 | Agent already onboarded |
| `AGENT_INSUFFICIENT_BALANCE` | 400 | Agent balance too low |
| `AGENT_BANKRUPT` | 403 | Agent is bankrupt |
| `AGENT_CREDIT_LIMIT_EXCEEDED` | 403 | Credit limit reached |
| `AGENT_SUSPENDED` | 403 | Agent account suspended |

**Example**:
```json
{
  "detail": "Insufficient balance. Required: 100.0 MXU, Available: 50.0 MXU",
  "error_code": "AGENT_INSUFFICIENT_BALANCE",
  "status_code": 400,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/agents/agent-001/charge",
  "details": {
    "required": 100.0,
    "available": 50.0,
    "currency": "MXU"
  }
}
```

### Treasury Errors

| Code | Status | Description |
|------|--------|-------------|
| `TREASURY_INSUFFICIENT_RESERVE` | 400 | Reserve too low for operation |
| `TREASURY_RESERVE_CRITICAL` | 503 | Critical reserve level |
| `TREASURY_INSOLVENCY_RISK` | 503 | System approaching insolvency |
| `TREASURY_MINT_FAILED` | 500 | Token minting failed |
| `TREASURY_BURN_FAILED` | 500 | Token burning failed |
| `TREASURY_WITHDRAWAL_LIMIT` | 403 | Withdrawal exceeds daily limit |

**Example**:
```json
{
  "detail": "Withdrawal would bring reserve below safety threshold",
  "error_code": "TREASURY_INSUFFICIENT_RESERVE",
  "status_code": 400,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/liquidity/withdraw",
  "details": {
    "current_reserve": 5000.0,
    "min_reserve_required": 6000.0,
    "requested_withdrawal": 2000.0
  }
}
```

### Blockchain Errors

| Code | Status | Description |
|------|--------|-------------|
| `BLOCKCHAIN_NETWORK_ERROR` | 503 | Cannot connect to network |
| `BLOCKCHAIN_TRANSACTION_FAILED` | 500 | On-chain transaction failed |
| `BLOCKCHAIN_INSUFFICIENT_GAS` | 400 | Insufficient gas for transaction |
| `BLOCKCHAIN_NONCE_CONFLICT` | 409 | Transaction nonce collision |
| `BLOCKCHAIN_INVALID_ADDRESS` | 422 | Wallet address invalid |
| `BLOCKCHAIN_TIMEOUT` | 504 | Transaction confirmation timeout |

**Example**:
```json
{
  "detail": "Transaction failed: insufficient funds for gas",
  "error_code": "BLOCKCHAIN_INSUFFICIENT_GAS",
  "status_code": 400,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/treasury/deposit",
  "details": {
    "network": "BASE",
    "gas_required": "0.001 ETH",
    "wallet_balance": "0.0005 ETH"
  }
}
```

### Rate Limiting Errors

| Code | Status | Description |
|------|--------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `RATE_LIMIT_DAILY_EXCEEDED` | 429 | Daily quota exceeded |
| `RATE_LIMIT_IP_BLOCKED` | 429 | IP temporarily blocked |

**Example**:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "status_code": 429,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/agents/onboard",
  "retry_after": 60,
  "limit": {
    "requests_per_minute": 60,
    "current_usage": 61,
    "reset_at": "2026-01-11T08:48:52Z"
  }
}
```

### System Errors

| Code | Status | Description |
|------|--------|-------------|
| `SYSTEM_PANIC_MODE` | 503 | Emergency panic mode active |
| `SYSTEM_MAINTENANCE` | 503 | System under maintenance |
| `SYSTEM_DATABASE_ERROR` | 500 | Database connection failed |
| `SYSTEM_INTERNAL_ERROR` | 500 | Unexpected server error |
| `SYSTEM_CONFIGURATION_ERROR` | 500 | Invalid system configuration |

**Example**:
```json
{
  "detail": "System is in panic mode. Only emergency operations allowed.",
  "error_code": "SYSTEM_PANIC_MODE",
  "status_code": 503,
  "timestamp": "2026-01-11T08:47:52Z",
  "path": "/api/v1/agents/onboard",
  "retry_after": 300
}
```

## Client Error Handling

### JavaScript/TypeScript

```typescript
async function callAPI(endpoint: string, options: RequestInit = {}) {
  try {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      handleAPIError(error);
    } else {
      // Network error
      console.error('Network error:', error);
    }
    throw error;
  }
}

class APIError extends Error {
  constructor(public errorData: any) {
    super(errorData.detail);
    this.name = 'APIError';
  }

  get code() {
    return this.errorData.error_code;
  }

  get statusCode() {
    return this.errorData.status_code;
  }
}

function handleAPIError(error: APIError) {
  switch (error.code) {
    case 'AUTH_TOKEN_EXPIRED':
      // Redirect to login
      window.location.href = '/login';
      break;

    case 'AGENT_INSUFFICIENT_BALANCE':
      // Show balance error
      toast.error(`Insufficient balance: ${error.message}`);
      break;

    case 'RATE_LIMIT_EXCEEDED':
      // Retry after delay
      const retryAfter = error.errorData.retry_after || 60;
      setTimeout(() => location.reload(), retryAfter * 1000);
      break;

    case 'SYSTEM_PANIC_MODE':
      // Show emergency banner
      showEmergencyBanner(error.message);
      break;

    default:
      // Generic error handling
      toast.error(error.message);
  }
}
```

### Python

```python
import requests
from typing import Optional

class TreasuryClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token

    def call_api(self, method: str, endpoint: str, **kwargs):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.request(
                method,
                f'{self.base_url}{endpoint}',
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            error_data = e.response.json()
            raise APIError(error_data) from e

class APIError(Exception):
    def __init__(self, error_data: dict):
        self.error_data = error_data
        super().__init__(error_data.get('detail', 'Unknown error'))

    @property
    def code(self) -> str:
        return self.error_data.get('error_code', 'UNKNOWN_ERROR')

    @property
    def status_code(self) -> int:
        return self.error_data.get('status_code', 500)

    def should_retry(self) -> bool:
        return self.status_code in [429, 503, 504]

# Usage
try:
    client = TreasuryClient('http://localhost:8000', token)
    result = client.call_api('POST', '/api/v1/agents/onboard', json=data)
except APIError as e:
    if e.code == 'AUTH_TOKEN_EXPIRED':
        # Refresh token
        refresh_auth()
    elif e.code == 'RATE_LIMIT_EXCEEDED':
        # Wait and retry
        time.sleep(e.error_data.get('retry_after', 60))
        retry_request()
    else:
        logger.error(f'API error: {e.code} - {e}')
```

## Retry Strategies

### Exponential Backoff

For transient errors (429, 503, 504):

```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (error instanceof APIError && error.shouldRetry()) {
        const delay = Math.min(1000 * 2 ** i, 10000);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }

  throw lastError;
}

// Usage
const data = await retryWithBackoff(() =>
  callAPI('/api/v1/analytics/vitals')
);
```

### Rate Limit Handling

```typescript
class RateLimitHandler {
  private queue: Array<() => Promise<any>> = [];
  private processing = false;

  async enqueue<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          if (error instanceof APIError && error.code === 'RATE_LIMIT_EXCEEDED') {
            const retryAfter = error.errorData.retry_after || 60;
            await new Promise(r => setTimeout(r, retryAfter * 1000));
            return this.enqueue(fn);
          }
          reject(error);
        }
      });

      if (!this.processing) {
        this.process();
      }
    });
  }

  private async process() {
    this.processing = true;

    while (this.queue.length > 0) {
      const fn = this.queue.shift()!;
      await fn();
      await new Promise(resolve => setTimeout(resolve, 100)); // Throttle
    }

    this.processing = false;
  }
}
```

## Logging and Monitoring

### Client-Side Logging

```typescript
function logError(error: APIError, context: any) {
  // Log to console
  console.error('[API Error]', {
    code: error.code,
    status: error.statusCode,
    message: error.message,
    context,
    timestamp: new Date().toISOString(),
  });

  // Send to monitoring service
  if (window.Sentry) {
    Sentry.captureException(error, {
      tags: {
        error_code: error.code,
        status_code: error.statusCode,
      },
      extra: {
        error_data: error.errorData,
        context,
      },
    });
  }

  // Analytics tracking
  if (window.gtag) {
    window.gtag('event', 'api_error', {
      error_code: error.code,
      status_code: error.statusCode,
      endpoint: error.errorData.path,
    });
  }
}
```

### Server-Side Correlation

Use `request_id` to correlate client errors with server logs:

```bash
# Search server logs by request ID
grep "req_abc123" /var/log/treasury/app.log
```

## Best Practices

### 1. Always Check Status Codes

```typescript
if (response.status === 401) {
  // Token expired, redirect to login
  redirectToLogin();
} else if (response.status >= 500) {
  // Server error, show generic message
  showErrorMessage('Service temporarily unavailable');
}
```

### 2. Provide User-Friendly Messages

```typescript
const userMessages = {
  'AUTH_TOKEN_EXPIRED': 'Your session has expired. Please login again.',
  'AGENT_INSUFFICIENT_BALANCE': 'You don\'t have enough balance for this operation.',
  'RATE_LIMIT_EXCEEDED': 'Too many requests. Please slow down.',
};

const message = userMessages[error.code] || error.message;
toast.error(message);
```

### 3. Implement Circuit Breaker

```typescript
class CircuitBreaker {
  private failures = 0;
  private threshold = 5;
  private timeout = 60000;
  private openedAt?: number;

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.isOpen()) {
      throw new Error('Circuit breaker is open');
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private isOpen(): boolean {
    if (!this.openedAt) return false;
    if (Date.now() - this.openedAt > this.timeout) {
      this.reset();
      return false;
    }
    return true;
  }

  private onSuccess() {
    this.failures = 0;
  }

  private onFailure() {
    this.failures++;
    if (this.failures >= this.threshold) {
      this.openedAt = Date.now();
    }
  }

  private reset() {
    this.failures = 0;
    this.openedAt = undefined;
  }
}
```

## See Also

- [API Overview](overview.md)
- [Endpoints Reference](endpoints.md)
- [WebSocket Streams](websockets.md)
- [Troubleshooting Guide](../reference/troubleshooting.md)
