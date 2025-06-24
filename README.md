# Ethyr - AI-Powered Ethereum Address Scanner

A chrome extension for analyzing Ethereum addresses, smart contracts, and tokens using advanced AI detection and on-chain analysis.

## Overview

Ethyr is a personal tool I developed to help analyze Ethereum addresses and contracts for potential risks and gather detailed insights. While it started as a personal project to assist with my own blockchain interactions, I've decided to share it with the community to help others make more informed decisions when interacting with the Ethereum ecosystem.

## Tech Stack

### Frontend
- React 18.2.0 with TypeScript 4.9.5
- Tailwind CSS 3.3.5 for styling
- Vite 4.5.0 for build tooling
- Chrome Extensions Manifest V3
- Web3.js 4.2.2 for blockchain interactions
- Framer Motion 12.18.1 for animations
- Heroicons for UI elements

### Backend
- Python 3.11+
- FastAPI 0.104.1 with Uvicorn 0.24.0
- Web3.py 6.11.3 for Ethereum interaction
- python-dotenv 1.0.0 for environment management
- aiohttp 3.9.1 for async HTTP requests
- Pydantic 1.10.13 for data validation

### AI/ML
- Hugging Face Transformers for model inference
- Mistral 7B for natural language explanations
- PyTorch for deep learning models
- PyTorch Geometric for graph neural networks
- Custom Models:
  - TLMG4ETH: Transaction Language Model with Graph Neural Network
  - MetaIFD: Meta-Interaction Fraud Detection
- Risk Detection Pipeline with heuristic rules

### Blockchain Integration
- Ethereum Mainnet
- Etherscan API
- Alchemy API
- Uniswap V2/V3 integration
- ERC20/ERC721 standard support
- eth-abi 5.0.0 for ABI encoding/decoding
- eth-account 0.9.0 for account management
- eth-typing 3.5.0 and eth-utils 2.2.0

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 16+
- Chrome Browser
- Ethereum API Keys (see API Keys section)

### Backend Setup
1. Clone the repository
```bash
git clone https://github.com/wqschain/ethyr.git
cd ethyr
```

2. Set up Python environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
```

3. Download model files
```bash
python download_models.py
```

4. Set up environment variables
Create a `.env` file in the backend directory with:
```
ETHERSCAN_API_KEY=your_key_here
ALCHEMY_API_KEY=your_key_here
```

### Frontend Setup
1. Install dependencies
```bash
cd extension
npm install
```

2. Build the extension
```bash
npm run build
```

3. Load the extension in Chrome:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `extension/dist` directory

## API Keys

You'll need the following API keys:
- [Etherscan API Key](https://etherscan.io/apis)
- [Alchemy API Key](https://www.alchemy.com/)

## Usage

1. Click the Ethyr extension icon in Chrome
2. Enter an Ethereum address or contract
3. View the comprehensive analysis and risk assessment

## Features

### Smart Contract Analysis
- Contract verification status check
- Source code analysis and risk detection
- Token contract detection and analysis
- Ownership and permission analysis
- Mint/burn event tracking
- Liquidity lock verification

### Token Analysis
- Market data (price, volume, liquidity)
- Holder activity metrics and whale analysis
- Trading pattern detection
- DEX distribution analysis
- Buy/sell ratio tracking
- Contract interaction analysis

### Wallet Analysis
- Transaction history and patterns
- ETH balance and value flow tracking
- DeFi protocol interactions
- Unique address interactions
- Gas usage analysis

### Risk Assessment
- AI-powered risk scoring
- Detailed risk explanations
- Risk tier classification
- Pattern-based threat detection
- Multi-factor security analysis
- Historical behavior analysis

### User Interface
- Clean, modern design with animated elements
- Real-time scanning visualization
- Tabbed interface for different analysis views
- Detailed metrics and statistics display
- Interactive data visualization
- Mobile-responsive layout

## Technical Architecture

### Frontend (Chrome Extension)
- React-based UI with TypeScript
- Real-time blockchain data visualization
- Interactive analysis dashboard
- Animated background with node visualization
- Metallic UI elements for better user experience

### Backend (Python FastAPI)
- FastAPI server for handling blockchain queries
- Advanced risk detection pipeline
- Integration with Ethereum nodes
- Caching layer for improved performance
- Comprehensive blockchain utilities


## v1 Limitations

Please note that this is version 1 of the tool and has some limitations:

### Performance
- Some analyses may take a few seconds to complete
- Complex contracts may require additional processing time

### Feature Stability
- Token price data may have delays
- Some advanced contract interactions may not be fully analyzed
- Risk assessment is based on known patterns and may not catch new types of risks

### Analysis Accuracy
- Risk scores are indicative and should not be the sole basis for decisions
- Market data accuracy depends on available liquidity and sources
- Some contract features may require manual verification

## Contact & Support

For questions, suggestions, or issues:
- Twitter: [@wqschain](https://x.com/wqschain)
- GitHub Issues: [Create an issue](https://github.com/wqschain/ethyr/issues)

## Disclaimer

The information provided by Ethyr is for informational purposes only and should not be considered as financial advice. Always conduct your own research and due diligence before interacting with any smart contracts or tokens.

## License

MIT License - See LICENSE file for details

## Project Structure

```
Ethyr/
├── backend/                 # Python FastAPI backend
│   ├── app.py              # Main FastAPI application
│   ├── blockchain_utils.py # Blockchain interaction utilities
│   └── models/             # AI models and analysis pipelines
│       ├── mistral/        # Mistral 7B model files
│       ├── meta_ifd/       # Meta-Interaction Fraud Detection
│       └── tlmg4eth/       # Transaction Language Model
├── extension/              # Chrome extension frontend
│   ├── src/               # React TypeScript source
│   │   ├── components/    # UI components
│   │   └── styles/        # CSS and styling
│   └── public/            # Static assets
```

## AI Models Used

### Mistral 7B
- Source: [Mistral AI](https://mistral.ai/)
- Model: [mistralai/Mistral-7B-v0.1](https://huggingface.co/mistralai/Mistral-7B-v0.1)
- Usage: Primary language model for analyzing contract behavior, generating risk explanations, and providing detailed insights about addresses and tokens.
- Selection Rationale: Chosen for its strong performance in understanding and analyzing complex patterns in blockchain data, while being efficient enough to run in a production environment.

### Custom Models

#### TLMG4ETH (Transaction Language Model + Graph Neural Network)
- Custom implementation combining transformer-based language models with graph neural networks
- Specifically designed for Ethereum transaction analysis
- Uses attention mechanisms to identify significant transaction patterns
- Incorporates graph structure of transaction networks for better risk assessment

#### MetaIFD (Meta-Interaction Fraud Detection)
- Custom model for detecting fraudulent patterns in token and contract interactions
- Uses meta-learning approach to identify suspicious transaction patterns
- Incorporates multiple types of blockchain interactions for comprehensive analysis

Note: The analysis and predictions provided by these models may not be 100% accurate and should be used as one of many tools in your research process.

## Project Demo

This is a quick demo of the project. Click below to watch it on YouTube:

[![Watch the Demo](https://img.youtube.com/vi/spL9O-oQoso/hqdefault.jpg)](https://www.youtube.com/watch?v=spL9O-oQoso)

## Personal Note
I created Ethyr as a tool to help me analyze blockchain addresses and contracts more efficiently. As someone actively involved in the Ethereum ecosystem, I found myself repeatedly performing the same checks and analysis when interacting with new contracts or addresses. This tool automates that process and provides a comprehensive overview of potential risks and important metrics. 
