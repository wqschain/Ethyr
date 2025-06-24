from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple
import json

from config import BERT4ETH_MODEL

class BERT4ETHPredictor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(BERT4ETH_MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(BERT4ETH_MODEL)
        self.model.eval()

    def _format_features(self, features: dict) -> str:
        """Format features dictionary into a string for BERT input."""
        feature_list = []
        
        if features["is_contract"]:
            # Contract-specific features
            contract_info = features["contract_info"]
            feature_list.extend([
                f"Contract {'is' if contract_info['is_verified'] else 'is not'} verified",
                f"Contract name: {contract_info['contract_name'] or 'Unknown'}",
            ])
            
            # Mint activity
            mint_data = features["mint_activity"]
            if mint_data:
                feature_list.extend([
                    f"Total mints: {mint_data['total_mints']}",
                    f"Total burns: {mint_data['total_burns']}"
                ])
            
            # Token info
            token_data = features["token_info"]
            if token_data:
                feature_list.extend([
                    f"Total supply: {token_data['total_supply']}",
                    f"Recent transfers: {token_data['recent_transfers']}",
                    f"Unique holders: {token_data['unique_holders']}"
                ])
            
            # Honeypot simulation
            honeypot_data = features["honeypot_simulation"]
            if honeypot_data:
                feature_list.append(
                    f"Token {'can' if honeypot_data['can_sell'] else 'cannot'} be sold"
                )
        else:
            feature_list.append("This is a wallet address")
        
        return " | ".join(feature_list)

    def classify_fraud(self, features: dict) -> Tuple[float, str]:
        """Classify the fraud probability of an address based on its features."""
        # Format features into text
        feature_text = self._format_features(features)
        
        # Tokenize and prepare input
        inputs = self.tokenizer(
            feature_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Get model prediction
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)
            fraud_score = probabilities[0][1].item()  # Assuming binary classification
        
        # Determine label based on score
        if fraud_score <= 0.30:
            label = "Safe"
        elif fraud_score <= 0.70:
            label = "Moderate"
        else:
            label = "Fraudulent"
        
        return fraud_score, label

# Initialize the predictor
predictor = BERT4ETHPredictor() 