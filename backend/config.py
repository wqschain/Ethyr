from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from web3 import AsyncWeb3, Web3
from web3.providers.async_rpc import AsyncHTTPProvider

# Load environment variables from both current and parent directory
current_dir = Path(__file__).parent
parent_dir = current_dir.parent

# Try loading from current directory first, then parent
load_dotenv(current_dir / '.env')
load_dotenv(parent_dir / '.env')

print("Current directory:", current_dir)
print("Parent directory:", parent_dir)
print("Environment variables after loading:")
print("ALCHEMY_URL:", os.getenv('ALCHEMY_URL'))
print("ALCHEMY_API_KEY:", os.getenv('ALCHEMY_API_KEY'))
print("ETHERSCAN_API_KEY:", os.getenv('ETHERSCAN_API_KEY'))

# API Keys and URLs
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ALCHEMY_URL = os.getenv("ALCHEMY_URL")

# Risk Score Thresholds
RISK_THRESHOLDS = {
    "SAFE": 0.30,
    "MODERATE": 0.70,
    # Anything above MODERATE is HIGH_RISK
}

# Model Constants
MISTRAL_MODEL = "mistralai/Mistral-7B-v0.1"

# Blockchain Constants
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TRANSFER_EVENT_SIGNATURE = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # keccak256("Transfer(address,address,uint256)")

class ModelConfig(BaseModel):
    """Configuration for ML models"""
    num_features: int = Field(default=256, description="Input feature dimension")
    hidden_dim: int = Field(default=256, description="Hidden layer dimension")
    num_heads: int = Field(default=8, description="Number of attention heads")
    num_layers: int = Field(default=4, description="Number of transformer layers")
    max_seq_length: int = Field(default=128, description="Maximum sequence length")

class APIConfig(BaseModel):
    """Configuration for API endpoints"""
    ALCHEMY_URL: str = Field(..., description="Alchemy endpoint URL")
    ETHERSCAN_API_KEY: str = Field(..., description="Etherscan API key")
    ETHERSCAN_URL: str = Field(default="https://api.etherscan.io/api", description="Etherscan API URL")

class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Load environment variables
        load_dotenv()
        
        # Debug: Print environment variables
        print("Environment variables:")
        print("ALCHEMY_URL:", os.getenv('ALCHEMY_URL'))
        print("ETHERSCAN_API_KEY:", os.getenv('ETHERSCAN_API_KEY'))
        
        # Get Alchemy URL
        self.alchemy_url = os.getenv('ALCHEMY_URL')
        if not self.alchemy_url:
            raise ValueError("ALCHEMY_URL not found in environment variables")
            
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        if not self.etherscan_api_key:
            raise ValueError("ETHERSCAN_API_KEY not found in environment variables")

        # Initialize Web3 provider with Alchemy
        self.w3 = AsyncWeb3(AsyncHTTPProvider(
            self.alchemy_url,
            request_kwargs={
                'headers': {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                }
            }
        ))

        # Extract Alchemy API key from URL for other services
        self.alchemy_api_key = self.alchemy_url.split('/')[-1]

        # Model parameters
        self.model_params = {
            'hidden_dim': 128,
            'num_features': 10,
            'num_classes': 2,
            'dropout': 0.2
        }

        # Cache settings
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # API endpoints
        self.etherscan_api = f"https://api.etherscan.io/api"
        
        # Initialize cache
        self.cache = {}
        
        # Model Constants
        self.MISTRAL_MODEL = "facebook/opt-350m"  # Using a smaller model that's easier to load
        
        # Blockchain Constants
        self.TRANSFER_EVENT_SIGNATURE = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        self.ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
        
        # Model Parameters
        model_config = ModelConfig()
        self.num_features = model_config.num_features
        self.hidden_dim = model_config.hidden_dim
        self.num_heads = model_config.num_heads
        self.num_layers = model_config.num_layers
        self.max_seq_length = model_config.max_seq_length
        
        # Directory Setup
        self.base_dir = Path(__file__).parent
        self.model_dir = self.base_dir / "models"
        
        # Create necessary directories
        self.model_dir.mkdir(exist_ok=True)
        
        # Risk Assessment Thresholds
        self.risk_thresholds = {
            "SAFE": 0.3,
            "MODERATE": 0.7
        }
        
        self._initialized = True
    
    def get_risk_tier(self, score: float) -> str:
        """Map a risk score to a risk tier."""
        if score <= self.risk_thresholds["SAFE"]:
            return "Safe"
        elif score <= self.risk_thresholds["MODERATE"]:
            return "Moderate Risk"
        return "High Risk"
    
    @property
    def api_config(self) -> APIConfig:
        """Get API configuration"""
        return APIConfig(
            ALCHEMY_URL=self.alchemy_url,
            ETHERSCAN_API_KEY=self.etherscan_api_key,
            ETHERSCAN_URL=self.etherscan_api
        )
    
    @property
    def model_parameters(self) -> Dict:
        """Get model parameters"""
        return {
            "num_features": self.num_features,
            "hidden_dim": self.hidden_dim,
            "num_heads": self.num_heads,
            "num_layers": self.num_layers,
            "max_seq_length": self.max_seq_length
        } 