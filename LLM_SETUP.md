# LLM Setup Guide for AI Trading Agents

## Overview
The AI Trading System uses real LLM agents powered by OpenAI GPT-3.5-turbo (with fallback to mock responses for demo).

## Quick Setup

### 1. OpenAI Configuration (Recommended)
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Get OpenAI API Key
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Add it to your environment

### 3. Test the System
1. Start the backend: `uvicorn backend.app:app --reload --port 8000`
2. Start the frontend: `streamlit run streamlit_app.py --server.port 8501`
3. Register agents and test AI chat

## Agent Capabilities

### 🎯 Trigger Agent
- Analyzes trading goals and constraints
- Provides risk assessment (1-10 scale)
- Determines if opportunities should be pursued

### 🧠 Expert Trader Agent  
- Deep market analysis and trading strategies
- Technical and fundamental analysis
- Entry/exit point recommendations

### ⚠️ Risk Evaluator Agent
- Comprehensive risk assessment
- Risk mitigation strategies
- Portfolio optimization

### 💼 Trader Agent
- Synthesizes recommendations
- Makes final trading decisions
- Execution planning

## Fallback Mode
If no OpenAI API key is provided, the system uses mock LLM responses for demonstration purposes.

## Alternative LLM Providers
You can modify `backend/llm_agent_handlers.py` to use:
- Anthropic Claude
- Hugging Face models
- Local LLMs (Ollama, etc.)
- Azure OpenAI

## Cost Considerations
- GPT-3.5-turbo: ~$0.002 per 1K tokens
- Typical agent response: 200-500 tokens
- Estimated cost per interaction: $0.001-0.002 

Human → "I want to trade AAPL with low risk"
    ↓
🎯 Trigger AI → Analyzes goals, assesses risk (7/10), recommends proceeding
    ↓  
🧠 Expert AI → "AAPL showing bullish momentum, recommend swing trade with..."
    ↓
⚠️ Risk AI → "Strategy has 6/10 risk, suggest 2% position size with stop-loss..."
    ↓
💼 Trader AI → "Final recommendation: Buy AAPL, 2% allocation, stop at $150..."
    ↓
Human ← Gets comprehensive AI-powered trading strategy 