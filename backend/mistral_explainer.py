from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Dict
import json

from config import MISTRAL_MODEL

class MistralExplainer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MISTRAL_MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(MISTRAL_MODEL)
        self.model.eval()

    def _build_prompt(self, features: Dict, score: float, label: str) -> str:
        """Build a prompt for Mistral based on address features and fraud analysis."""
        prompt = """<s>[INST] You are an Ethereum smart contract fraud analyst. Given the following data about an Ethereum address, explain why it may or may not be safe to interact with. Be specific about the risk factors and provide a clear recommendation. Here's the data:

"""
        # Add contract/wallet status
        if features["is_contract"]:
            prompt += "Type: Smart Contract\n"
            contract_info = features["contract_info"]
            
            # Add verification status
            prompt += f"Verified: {contract_info['is_verified']}\n"
            if contract_info["contract_name"]:
                prompt += f"Contract Name: {contract_info['contract_name']}\n"
            
            # Add mint activity if available
            if features["mint_activity"]:
                mint_data = features["mint_activity"]
                prompt += f"Mints: {mint_data['total_mints']}\n"
                prompt += f"Burns: {mint_data['total_burns']}\n"
            
            # Add token info if available
            if features["token_info"]:
                token_data = features["token_info"]
                prompt += f"Total Supply: {token_data['total_supply']}\n"
                prompt += f"Recent Transfers: {token_data['recent_transfers']}\n"
                prompt += f"Unique Holders: {token_data['unique_holders']}\n"
            
            # Add honeypot simulation results
            if features["honeypot_simulation"]:
                honeypot = features["honeypot_simulation"]
                prompt += f"Can Sell Tokens: {honeypot['can_sell']}\n"
        else:
            prompt += "Type: Wallet Address\n"
        
        # Add risk assessment
        prompt += f"\nRisk Score: {score:.2%}\n"
        prompt += f"Risk Label: {label}\n"
        
        prompt += "\nBased on this data, explain the risk assessment and provide recommendations for users. [/INST]"
        return prompt

    def generate_explanation(self, features: Dict, score: float, label: str) -> str:
        """Generate a natural language explanation of the address risk assessment."""
        # Build the prompt
        prompt = self._build_prompt(features, score, label)
        
        # Generate explanation
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=2048,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode and clean up the generated text
        explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated explanation (remove the prompt)
        explanation = explanation.split("[/INST]")[-1].strip()
        
        return explanation

# Initialize the explainer
explainer = MistralExplainer() 