# Multi-Agent Trading System with DID and Verifiable Credentials

This project implements a decentralized trading system with three specialized agents:

1. **Trigger Agent**: Initiates trading requests and provides trading goals
2. **Expert Trader Agent**: Processes trading goals and executes trades
3. **Risk Evaluator Agent**: Evaluates and assesses trading risks

## Architecture

The system uses Decentralized Identifiers (DIDs) and Verifiable Credentials (VCs) for secure agent communication and identity verification. The workflow is:

1. Trigger Agent initiates a trading request with its DID
2. Expert Trader Agent verifies Trigger Agent's credentials
3. Risk Evaluator Agent assesses the trading proposal
4. Expert Trader Agent processes the final decision and responds

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the system:
```bash
python main.py
```

## Components

- `agents/`: Contains individual agent implementations
- `did/`: DID and VC handling
- `trading/`: Trading logic and market analysis
- `risk/`: Risk evaluation system
- `api/`: API endpoints for agent communication

## Security

- All agents use DIDs for identity
- Verifiable Credentials ensure trust between agents
- Secure communication channels between agents
- Risk evaluation before any trade execution 