# A2A - AI Agent Trading System with Blockchain Integration

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ethereum](https://img.shields.io/badge/Ethereum-Sepolia-orange.svg)](https://sepolia.etherscan.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/hsinghb/A2A-AI-Trading-System)

A decentralized AI trading system that combines artificial intelligence agents with Ethereum blockchain technology for secure, transparent, and autonomous trading operations.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized AI agents for different trading functions
- **Blockchain Integration**: Ethereum-based agent registry and DID authentication
- **Risk Management**: Automated risk evaluation and assessment
- **Decentralized Identity**: DID-based agent authentication and verification
- **Real-time Trading**: Live market analysis and trading execution
- **Web Interface**: Streamlit-based user interface for system monitoring
- **Smart Contracts**: Solidity contracts for agent registration and management

## 🏗️ Architecture

The system consists of three main AI agents working together:

1. **Trigger Agent**: Initiates trading requests and defines trading goals
2. **Expert Trader Agent**: Processes trading strategies and executes trades
3. **Risk Evaluator Agent**: Assesses risks and provides risk mitigation strategies

### System Components

```
A2A/
├── agents/           # AI agent implementations
├── backend/          # Core system backend
├── blockchain/       # Ethereum integration
├── contracts/        # Smart contracts
├── frontend/         # Web interface
├── api/             # REST API endpoints
├── scripts/         # Utility scripts
└── docs/            # Documentation
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Ethereum wallet with Sepolia testnet ETH
- Infura API key (or other Ethereum provider)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/hsinghb/A2A-AI-Trading-System.git
   cd A2A-AI-Trading-System
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Deploy smart contracts**
   ```bash
   python scripts/deploy_registry.py
   ```

6. **Start the system**
   ```bash
   ./start_system.sh
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Ethereum Configuration
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS=deployed_contract_address

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# System Configuration
DEBUG_MODE=true
LOG_LEVEL=INFO
```

### Smart Contract Deployment

The system uses a custom `AgentRegistry` smart contract for agent management:

```bash
# Compile contracts
python scripts/compile_contract.py

# Deploy to Sepolia testnet
python scripts/deploy_registry.py
```

## 🚀 Usage

### Starting the System

```bash
# Start with virtual environment
./start_system.sh

# Start without virtual environment
./start_system_no_venv.sh
```

### Web Interface

Access the Streamlit interface at: `http://localhost:8501`

### API Endpoints

- `GET /`: System status
- `POST /trading/process`: Process trading requests
- `GET /agents`: List registered agents
- `POST /agents/register`: Register new agent

## 📊 System Status

The system provides real-time monitoring through:

- **Agent Registry**: Track all registered agents on the blockchain
- **Trading Logs**: Monitor trading activities and decisions
- **Risk Metrics**: View current risk assessments
- **Performance Analytics**: Track system performance

## 🔒 Security Features

- **DID Authentication**: Decentralized identifiers for agent identity
- **JWT Tokens**: Secure communication between agents
- **Smart Contract Verification**: On-chain agent registration
- **Risk Assessment**: Automated risk evaluation before trades
- **Audit Trail**: Complete transaction history on blockchain

## 📚 Documentation

- [Architecture Design](ARCHITECTURE_DESIGN.md) - Detailed system architecture
- [Deployment Guide](DEPLOYMENT_DOCUMENTATION.md) - Deployment instructions
- [Technical Specification](docs/technical_spec.md) - Technical details
- [Ethereum Integration](docs/ethereum_agent_network.md) - Blockchain integration guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Ethereum Foundation for blockchain infrastructure
- OpenAI and Anthropic for AI capabilities
- Streamlit for the web interface framework
- The open-source community for various dependencies

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the deployment guide for setup issues

---

**Note**: This is a research and development project. Use at your own risk and ensure compliance with local regulations before using for actual trading. 