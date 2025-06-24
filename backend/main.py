from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from web3 import Web3
from web3.types import ChecksumAddress
from typing import Optional, Dict, List, Union
from pathlib import Path

# Local imports
from models.risk_detection_pipeline import RiskDetectionPipeline
from blockchain_utils import fetch_address_data
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Ethyr API",
    description="API for analyzing Ethereum addresses for potential fraud",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
)

# Initialize configuration and pipeline
config = Config()
pipeline = RiskDetectionPipeline(config)

class TokenHolding(BaseModel):
    contract: str
    symbol: str
    name: str
    balance: float

class WalletMetrics(BaseModel):
    balance: float
    total_transactions: int
    first_tx_timestamp: Optional[str]
    last_tx_timestamp: Optional[str]
    unique_interacted_addresses: int
    incoming_tx_count: int
    outgoing_tx_count: int
    failed_tx_count: int
    total_received_eth: float
    total_sent_eth: float
    avg_gas_used: float
    total_gas_spent_eth: float
    token_holdings: List[TokenHolding]
    nft_holdings: int
    nft_transactions: int
    wallet_age_days: int

class DeFiProtocol(BaseModel):
    interaction_count: int
    total_value: float
    last_interaction: Optional[str]

class DeFiActivity(BaseModel):
    protocols: Dict[str, DeFiProtocol]
    total_interactions: int
    total_value_locked: float
    last_interaction: Optional[str]

class AddressRequest(BaseModel):
    address: str

class AddressResponse(BaseModel):
    type: str
    risk_score: float
    risk_tier: str
    explanation: List[str]
    summary: Dict
    features: Dict
    is_contract: bool
    is_token: bool
    token_info: Optional[Dict] = None
    wallet_metrics: Optional[WalletMetrics] = None
    defi_activity: Optional[DeFiActivity] = None

@app.post("/analyze", response_model=AddressResponse)
async def analyze_address(request: AddressRequest):
    try:
        # Validate Ethereum address
        if not Web3.is_address(request.address):
            return JSONResponse(
                status_code=400,
                content={
                    "type": "Error",
                    "risk_score": 0.0,
                    "risk_tier": "Unknown",
                    "explanation": ["Invalid Ethereum address format"],
                    "summary": {},
                    "features": {},
                    "is_contract": False,
                    "is_token": False,
                    "token_info": None,
                    "wallet_metrics": None,
                    "defi_activity": None
                }
            )
        
        # Fetch on-chain data
        address_data = await fetch_address_data(request.address)
        
        # If fetch_address_data returned an error response, return it directly
        if address_data.get("type") == "Error":
            return JSONResponse(
                status_code=500,
                content=address_data
            )
            
        # Format features into natural language for the models
        features_text = format_features_text(
            address_data["features"],
            address_data.get("wallet_metrics")
        )
        
        # Get risk analysis from pipeline
        risk_score, risk_tier, explanation = pipeline.analyze_address(
            address_data,
            features_text
        )
        
        # Prepare summary data
        summary = {
            "verified": address_data["features"].get("verified_contract", False),
            "creator_address": address_data["features"].get("owner_address"),
            "total_transactions": len(address_data.get("transactions", [])),
            "unique_interactions": len(set(
                tx["from"] for tx in address_data.get("transactions", [])
            ) | set(
                tx["to"] for tx in address_data.get("transactions", [])
            )),
            "total_value": address_data["features"].get("transfer_volume_24h", 0.0),
            "is_contract": address_data["features"].get("is_contract", False),
            "contract_age_days": address_data["features"].get("contract_age_days") if address_data["features"].get("is_contract") else None,
            "mint_events": address_data["features"].get("mint_event_count") if address_data["features"].get("is_contract") else None,
            "burn_events": address_data["features"].get("burn_event_count") if address_data["features"].get("is_contract") else None,
            "lp_locked": address_data["features"].get("lp_locked") if address_data["features"].get("is_contract") else None
        }
        
        response_data = {
            "type": address_data.get("type", "Unknown"),
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "explanation": explanation,
            "summary": summary,
            "features": address_data.get("features", {}),
            "is_contract": address_data.get("is_contract", False),
            "is_token": address_data.get("is_token", False),
            "token_info": address_data.get("token_info"),
            "wallet_metrics": address_data.get("wallet_metrics"),
            "defi_activity": address_data.get("defi_activity")
        }
        
        return response_data
        
    except Exception as e:
        error_response = {
            "type": "Error",
            "risk_score": 0.0,
            "risk_tier": "Unknown",
            "explanation": [f"Error analyzing address: {str(e)}"],
            "summary": {},
            "features": {},
            "is_contract": False,
            "is_token": False,
            "token_info": None,
            "wallet_metrics": None,
            "defi_activity": None
        }
        return JSONResponse(status_code=500, content=error_response)

@app.get("/analyze/{address}", response_model=AddressResponse)
async def analyze_address_get(address: str):
    try:
        # Validate Ethereum address
        if not Web3.is_address(address):
            return JSONResponse(
                status_code=400,
                content={
                    "type": "Error",
                    "risk_score": 0.0,
                    "risk_tier": "Unknown",
                    "explanation": ["Invalid Ethereum address format"],
                    "summary": {},
                    "features": {},
                    "is_contract": False,
                    "is_token": False,
                    "token_info": None,
                    "wallet_metrics": None,
                    "defi_activity": None
                }
            )
        
        # Fetch on-chain data
        address_data = await fetch_address_data(address)
        
        # If fetch_address_data returned an error response, return it directly
        if address_data.get("type") == "Error":
            return JSONResponse(
                status_code=500,
                content=address_data
            )
            
        # Format features into natural language for the models
        features_text = format_features_text(
            address_data["features"],
            address_data.get("wallet_metrics")
        )
        
        # Get risk analysis from pipeline
        risk_score, risk_tier, explanation = pipeline.analyze_address(
            address_data,
            features_text
        )
        
        # Prepare summary data
        summary = {
            "verified": address_data["features"].get("verified_contract", False),
            "creator_address": address_data["features"].get("owner_address"),
            "total_transactions": len(address_data.get("transactions", [])),
            "unique_interactions": len(set(
                tx["from"] for tx in address_data.get("transactions", [])
            ) | set(
                tx["to"] for tx in address_data.get("transactions", [])
            )),
            "total_value": address_data["features"].get("transfer_volume_24h", 0.0),
            "is_contract": address_data["features"].get("is_contract", False),
            "contract_age_days": address_data["features"].get("contract_age_days") if address_data["features"].get("is_contract") else None,
            "mint_events": address_data["features"].get("mint_event_count") if address_data["features"].get("is_contract") else None,
            "burn_events": address_data["features"].get("burn_event_count") if address_data["features"].get("is_contract") else None,
            "lp_locked": address_data["features"].get("lp_locked") if address_data["features"].get("is_contract") else None
        }
        
        response_data = {
            "type": address_data.get("type", "Unknown"),
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "explanation": explanation,
            "summary": summary,
            "features": address_data.get("features", {}),
            "is_contract": address_data.get("is_contract", False),
            "is_token": address_data.get("is_token", False),
            "token_info": address_data.get("token_info"),
            "wallet_metrics": address_data.get("wallet_metrics"),
            "defi_activity": address_data.get("defi_activity")
        }
        
        return response_data
        
    except Exception as e:
        error_response = {
            "type": "Error",
            "risk_score": 0.0,
            "risk_tier": "Unknown",
            "explanation": [f"Error analyzing address: {str(e)}"],
            "summary": {},
            "features": {},
            "is_contract": False,
            "is_token": False,
            "token_info": None,
            "wallet_metrics": None,
            "defi_activity": None
        }
        return JSONResponse(status_code=500, content=error_response)

def format_features_text(features: Dict, wallet_metrics: Optional[Dict] = None) -> str:
    """Format features into natural language for model input"""
    
    if features["is_contract"]:
        # Contract description
        text = f"""This is a{'n unverified' if not features['verified_contract'] else ' verified'} contract created {features['contract_age_days']} days ago"""
        
        # Add owner info
        if features["owner_address"]:
            text += f" by {features['owner_address']}"
            if features["is_owner_deployer"]:
                text += " (who is also the deployer)"
        
        # Add mint info
        if features["has_mint_privileges"]:
            text += f". The owner has mint privileges and there have been {features['mint_event_count']} mint events"
        
        # Add liquidity info
        text += f". Liquidity is {'not ' if not features['lp_locked'] else ''}locked"
        
        # Add honeypot info
        text += f". Honeypot test {'failed' if features['honeypot_result'] else 'passed'}"
        
        # Add burn and volume info
        text += f". There were {features['burn_event_count']} burn events"
        if features['transfer_volume_24h'] > 0:
            text += f" and {features['transfer_volume_24h']:.2f} ETH in transfer volume in the last 24 hours"
        
    else:
        # Wallet description
        daily_volume = 0.0
        if wallet_metrics:
            # Calculate 24h volume from total sent and received
            daily_volume = wallet_metrics.get('total_sent_eth', 0.0) + wallet_metrics.get('total_received_eth', 0.0)
        
        text = f"""This is a regular wallet address with {daily_volume:.2f} ETH in transfer volume"""
    
    return text

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if models are loaded
        if not hasattr(pipeline, "tlmg4eth") or not hasattr(pipeline, "mistral"):
            return {
                "status": "unhealthy",
                "detail": "Models not properly loaded"
            }
        
        return {
            "status": "healthy",
            "models": {
                "tlmg4eth": "loaded",
                "mistral": "loaded"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "detail": str(e)
        }

@app.get("/models/status")
async def model_status():
    """Get detailed model status"""
    return {
        "tlmg4eth": {
            "loaded": hasattr(pipeline, "tlmg4eth"),
            "device": str(next(pipeline.tlmg4eth.parameters()).device)
            if hasattr(pipeline, "tlmg4eth") else None
        },
        "mistral": {
            "loaded": hasattr(pipeline, "mistral"),
            "device": pipeline.mistral.device
            if hasattr(pipeline, "mistral") else None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 