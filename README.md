# Ethyr - AI-Powered Ethereum Address Scanner

A chrome extension for analyzing Ethereum addresses, smart contracts, and tokens using advanced AI detection and on-chain analysis.

## Overview

Ethyr is a personal tool I developed to help analyze Ethereum addresses and contracts for potential risks and gather detailed insights. While it started as a personal project to assist with my own blockchain interactions, I've decided to share it with the community to help others make more informed decisions when interacting with the Ethereum ecosystem.

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 16+
- Chrome Browser
- Ethereum API Keys (see API Keys section)

### Backend Setup
1. Clone the repository
```bash
git clone https://github.com/yourusername/ethyr.git
cd ethyr
```

2. Set up Python virtual environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Start the backend server
```bash
uvicorn app:app --reload
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

3. Load the extension in Chrome
- Open Chrome and navigate to `chrome://extensions/`
- Enable "Developer mode"
- Click "Load unpacked" and select the `extension/build` directory

## API Keys Required

The following API keys are needed for full functionality:

1. **Etherscan API Key**
   - Required for: Transaction history, contract verification
   - Get it from: [Etherscan](https://etherscan.io/apis)
   - Environment variable: `ETHERSCAN_API_KEY`

2. **Alchemy API Key**
   - Required for: Token metadata, NFT data
   - Get it from: [Alchemy](https://www.alchemy.com/)
   - Environment variable: `ALCHEMY_API_KEY`

## Usage

1. Click the Ethyr extension icon in Chrome
2. Enter an Ethereum address (wallet, contract, or token)
3. Click "Scan" to analyze
4. View results in different tabs:
   - Overview: General information and risk assessment
   - Tokens: Token-specific analysis (for token contracts) or holdings (for wallets)
   - DeFi: DEX information or DeFi protocol interactions

## Contributing

This is a personal project that I'm actively developing. While I appreciate interest in contributing, please note that I'm currently focused on implementing my vision for the tool. However, feel free to:

1. Report bugs by opening issues
2. Suggest features
3. Fork the project for your own use

## Contact & Support

- Twitter: [@wqschain](https://x.com/wqschain)
- For issues and feature requests, please use GitHub Issues

## Disclaimer

The analysis and predictions provided by Ethyr are based on available on-chain data and pattern recognition. This tool should be used as one of many resources in your research process, not as the sole decision-maker. Always conduct your own due diligence before interacting with any smart contracts or tokens.

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

## Version 1 Limitations

As this is the first version of Ethyr, there are some known limitations and features that may not work as intended:

1. Performance Limitations
   - Large token holder analysis may timeout for tokens with extensive transaction history
   - DEX volume calculations might be delayed for high-activity pools
   - Some contract analysis features may take longer than expected

2. Feature Stability
   - NFT analysis is currently limited and may not capture all NFT-related activities
   - Some DeFi protocol interactions might not be properly categorized
   - Whale analysis thresholds may need adjustment based on token specifics

3. UI/UX Considerations
   - The extension currently works best on desktop Chrome
   - Some animations might not render smoothly on lower-end devices
   - Real-time updates are not yet implemented

4. Analysis Accuracy
   - Risk scoring is based on current patterns and may need refinement
   - Some contract verification checks might have false positives
   - Market data might have slight delays or inconsistencies

Please note that this is an actively developed project, and these limitations will be addressed in future updates.

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

## Personal Note
I created Ethyr as a tool to help me analyze blockchain addresses and contracts more efficiently. As someone actively involved in the Ethereum ecosystem, I found myself repeatedly performing the same checks and analysis when interacting with new contracts or addresses. This tool automates that process and provides a comprehensive overview of potential risks and important metrics. 