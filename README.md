# README.md
# Financial Data Platform

A production-ready financial data platform with AI integration and agent-based architecture.

## Features

- **Multi-source Data Aggregation**: Intelligent failover across YFinance, Robin Stocks, Charles Schwab, SoFi, and IBKR
- **Real-time WebSocket Streaming**: Low-latency market data streaming
- **AI Assistant Integration**: Multiple AI models (Claude, ChatGPT, Gemini, Grok) with intelligent selection
- **Agent-Based Architecture**: Autonomous agents for tool creation, analysis, and orchestration
- **Time-Series Database**: TimescaleDB for efficient financial data storage
- **Advanced Caching**: Multi-layer caching with Redis
- **Model Context Protocol (MCP)**: Standardized tool interface for AI assistants
- **Comprehensive Security**: JWT authentication, rate limiting, encryption

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Clients   │────▶│  API Gateway │────▶│Rate Limiter │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Auth      │────▶│Cache Layer  │
                    └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────────────────────────┐
                    │     Orchestrator Agent          │
                    └─────────────────────────────────┘
                            │
                            ▼
                    ┌─────────────────────────────────┐
                    │      Data Aggregator            │
                    └─────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  TimescaleDB │
                    └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL with TimescaleDB
- Redis
- API keys for AI services

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/financial-data-platform.git
cd financial-data-platform
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Install dependencies:
```bash
make install
```

4. Initialize the database:
```bash
make init-db
```

5. Start services:
```bash
make docker-up
```

### Development

Run the development server:
```bash
make run-dev
```

Run tests:
```bash
make test
```

### Production Deployment

1. Build Docker images:
```bash
make docker-build
```

2. Deploy to Kubernetes:
```bash
make deploy-k8s
```

## API Documentation

### Authentication

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "password"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Market Data

```bash
# Get quote
curl -X GET http://localhost:5000/api/market/quote/AAPL \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get historical data
curl -X GET "http://localhost:5000/api/market/historical/AAPL?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### WebSocket Streaming

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'subscribe',
        symbols: ['AAPL', 'GOOGL'],
        data_types: ['quotes', 'news']
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## Agent System

### Available Agents

1. **Orchestrator Agent**: Coordinates all agent activities
2. **Tool Creator Agent**: Dynamically creates new MCP tools
3. **Agent Creator Agent**: Spawns new specialized agents
4. **Data Analysis Agent**: Performs complex data analysis
5. **Alert Monitor Agent**: Monitors conditions and triggers alerts

### Creating Custom Agents

```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("CustomAgent", "Description")
        
    async def process_message(self, message):
        # Process messages
        pass
```

## Examples

See the `examples/` directory for:
- Trading bot with AI decision-making
- Portfolio analyzer with risk assessment
- Real-time news monitoring system
- Web dashboard

## Monitoring

Access monitoring dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default password in .env)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support, email support@financial-platform.com or create an issue.
