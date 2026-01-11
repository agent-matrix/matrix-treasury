# WebSocket Streams

Real-time data streaming via WebSocket connections.

## Overview

Matrix Treasury provides WebSocket endpoints for real-time updates on:

- Treasury balance changes
- Agent transactions
- System health status
- Pending approvals
- Network events

## Connection

### Endpoint

```
ws://localhost:8000/ws/stream
```

### Authentication

WebSocket connections require JWT authentication via query parameter:

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws/stream?token=${token}`);
```

### Connection Events

```javascript
ws.onopen = () => {
  console.log('Connected to Matrix Treasury stream');
};

ws.onclose = (event) => {
  console.log('Disconnected:', event.code, event.reason);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

## Subscription Model

### Subscribe to Channels

After connection, subscribe to specific channels:

```javascript
// Subscribe to treasury updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'treasury'
}));

// Subscribe to agent transactions
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'transactions',
  agent_id: 'agent-001'  // Optional: filter by agent
}));

// Subscribe to system health
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'health'
}));
```

### Unsubscribe from Channels

```javascript
ws.send(JSON.stringify({
  type: 'unsubscribe',
  channel: 'treasury'
}));
```

## Available Channels

### 1. Treasury Channel

Real-time treasury balance and metrics updates.

**Channel**: `treasury`

**Message Format**:
```json
{
  "channel": "treasury",
  "event": "balance_update",
  "timestamp": "2026-01-11T08:47:52Z",
  "data": {
    "usdc_balance": 5432.50,
    "eur_balance": 2100.00,
    "btc_balance": 0.05,
    "mxu_supply": 100000.0,
    "coverage_ratio": 1.25,
    "health_status": "HEALTHY"
  }
}
```

**Events**:
- `balance_update` - Balance changed
- `deposit` - New deposit received
- `withdrawal` - Withdrawal executed
- `reserve_low` - Reserve below threshold
- `reserve_critical` - Critical reserve level

### 2. Transactions Channel

Real-time transaction feed.

**Channel**: `transactions`

**Filters**:
- `agent_id` - Filter by specific agent
- `tx_type` - Filter by transaction type
- `currency` - Filter by currency

**Message Format**:
```json
{
  "channel": "transactions",
  "event": "new_transaction",
  "timestamp": "2026-01-11T08:47:52Z",
  "data": {
    "id": 123,
    "agent_id": "agent-001",
    "type": "CHARGE",
    "amount": 10.0,
    "currency": "USDC",
    "network": "BASE",
    "description": "Compute charges",
    "status": "COMPLETED"
  }
}
```

**Events**:
- `new_transaction` - New transaction created
- `transaction_confirmed` - Transaction confirmed on-chain
- `transaction_failed` - Transaction failed

### 3. Agents Channel

Agent lifecycle events.

**Channel**: `agents`

**Message Format**:
```json
{
  "channel": "agents",
  "event": "agent_onboarded",
  "timestamp": "2026-01-11T08:47:52Z",
  "data": {
    "agent_id": "agent-001",
    "email": "agent001@example.com",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    "initial_balance": 100.0,
    "credit_score": 500
  }
}
```

**Events**:
- `agent_onboarded` - New agent registered
- `agent_balance_low` - Agent balance below threshold
- `agent_bankrupt` - Agent declared bankrupt
- `credit_score_changed` - Credit score updated

### 4. Health Channel

System health monitoring.

**Channel**: `health`

**Message Format**:
```json
{
  "channel": "health",
  "event": "health_update",
  "timestamp": "2026-01-11T08:47:52Z",
  "data": {
    "status": "HEALTHY",
    "autopilot_enabled": true,
    "panic_mode": false,
    "active_agents": 45,
    "pending_approvals": 2,
    "network_status": {
      "BASE": "online",
      "POLYGON": "online",
      "ARBITRUM": "degraded",
      "OPTIMISM": "online"
    }
  }
}
```

**Events**:
- `health_update` - Periodic health check (every 30s)
- `autopilot_toggled` - Autopilot mode changed
- `panic_mode_activated` - Emergency mode activated
- `network_issue` - Blockchain network problem

### 5. Approvals Channel

Pending approval notifications.

**Channel**: `approvals`

**Message Format**:
```json
{
  "channel": "approvals",
  "event": "new_approval",
  "timestamp": "2026-01-11T08:47:52Z",
  "data": {
    "id": 456,
    "agent": "agent-001",
    "action": "Large withdrawal",
    "cost": 500.0,
    "tx_kind": "WITHDRAWAL",
    "reason": "Exceeds daily limit",
    "status": "PENDING"
  }
}
```

**Events**:
- `new_approval` - New approval required
- `approval_granted` - Approval granted by admin
- `approval_denied` - Approval denied
- `approval_expired` - Approval timeout

## Client Implementation

### JavaScript/TypeScript

```typescript
class TreasuryStream {
  private ws: WebSocket;
  private token: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(token: string) {
    this.token = token;
    this.connect();
  }

  private connect() {
    this.ws = new WebSocket(`ws://localhost:8000/ws/stream?token=${this.token}`);

    this.ws.onopen = () => {
      console.log('Connected to Treasury stream');
      this.reconnectAttempts = 0;
      this.subscribeToChannels();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      console.log('Connection closed:', event.code);
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private subscribeToChannels() {
    this.subscribe('treasury');
    this.subscribe('transactions');
    this.subscribe('health');
  }

  subscribe(channel: string, filters?: Record<string, any>) {
    this.ws.send(JSON.stringify({
      type: 'subscribe',
      channel,
      ...filters
    }));
  }

  unsubscribe(channel: string) {
    this.ws.send(JSON.stringify({
      type: 'unsubscribe',
      channel
    }));
  }

  private handleMessage(message: any) {
    switch (message.channel) {
      case 'treasury':
        this.onTreasuryUpdate(message.data);
        break;
      case 'transactions':
        this.onTransaction(message.data);
        break;
      case 'health':
        this.onHealthUpdate(message.data);
        break;
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  disconnect() {
    this.ws.close();
  }

  // Event handlers (override these)
  onTreasuryUpdate(data: any) {}
  onTransaction(data: any) {}
  onHealthUpdate(data: any) {}
}

// Usage
const stream = new TreasuryStream(token);
stream.onTreasuryUpdate = (data) => {
  console.log('Treasury update:', data);
  updateDashboard(data);
};
```

### Python

```python
import asyncio
import websockets
import json

class TreasuryStream:
    def __init__(self, token: str):
        self.token = token
        self.uri = f"ws://localhost:8000/ws/stream?token={token}"
        self.ws = None

    async def connect(self):
        async with websockets.connect(self.uri) as websocket:
            self.ws = websocket

            # Subscribe to channels
            await self.subscribe('treasury')
            await self.subscribe('transactions')

            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                await self.handle_message(data)

    async def subscribe(self, channel: str, **filters):
        await self.ws.send(json.dumps({
            'type': 'subscribe',
            'channel': channel,
            **filters
        }))

    async def handle_message(self, message: dict):
        channel = message.get('channel')
        event = message.get('event')
        data = message.get('data')

        print(f"[{channel}] {event}:", data)

# Usage
async def main():
    token = "your-jwt-token"
    stream = TreasuryStream(token)
    await stream.connect()

asyncio.run(main())
```

### React Hook

```typescript
import { useEffect, useState } from 'react';

export function useTreasuryStream(token: string) {
  const [treasuryData, setTreasuryData] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/stream?token=${token}`);

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'subscribe', channel: 'treasury' }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.channel === 'treasury') {
        setTreasuryData(message.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [token]);

  return { treasuryData, connected };
}

// Component usage
function Dashboard() {
  const { data: user } = useAuthContext();
  const { treasuryData, connected } = useTreasuryStream(user.token);

  return (
    <div>
      <div>Status: {connected ? '🟢 Connected' : '🔴 Disconnected'}</div>
      {treasuryData && (
        <div>
          <div>Balance: ${treasuryData.usdc_balance}</div>
          <div>Health: {treasuryData.health_status}</div>
        </div>
      )}
    </div>
  );
}
```

## Best Practices

### 1. Reconnection Strategy

Implement exponential backoff for reconnections:

```javascript
const maxDelay = 30000; // 30 seconds
const delay = Math.min(1000 * 2 ** attempt, maxDelay);
```

### 2. Heartbeat/Ping

Send periodic pings to keep connection alive:

```javascript
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

### 3. Error Handling

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Log to monitoring service
  Sentry.captureException(error);
};
```

### 4. Message Queuing

Buffer messages during reconnection:

```javascript
const messageQueue = [];

function sendMessage(msg) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg));
  } else {
    messageQueue.push(msg);
  }
}
```

### 5. Subscription Management

Track subscriptions for reconnection:

```javascript
const subscriptions = new Set();

function subscribe(channel) {
  subscriptions.add(channel);
  ws.send(JSON.stringify({ type: 'subscribe', channel }));
}

function resubscribe() {
  subscriptions.forEach(channel => subscribe(channel));
}
```

## Performance Considerations

- **Throttle updates**: Limit UI updates to 60fps
- **Batch messages**: Group related updates
- **Selective subscriptions**: Only subscribe to needed channels
- **Connection pooling**: Reuse connections across components
- **Memory management**: Unsubscribe when components unmount

## Troubleshooting

### Connection Issues

**Problem**: Connection refused

```bash
# Check WebSocket port
netstat -an | grep 8000

# Verify backend is running
curl http://localhost:8000/api/v1/
```

**Problem**: Authentication failed

```javascript
// Check token validity
console.log('Token:', token);
console.log('Expires:', JSON.parse(atob(token.split('.')[1])).exp);
```

**Problem**: Frequent disconnections

```javascript
// Check network stability
ws.addEventListener('close', (event) => {
  console.log('Close code:', event.code);
  // 1000 = Normal closure
  // 1006 = Abnormal closure (network issue)
});
```

## See Also

- [API Overview](overview.md)
- [Endpoints Reference](endpoints.md)
- [Error Handling](errors.md)
- [Development Guide](../guides/development.md)
