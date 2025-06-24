import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, List, Optional
import os
import numpy as np
from pathlib import Path

# Relative imports from the models directory
from .tlmg4eth.model import TLMG4ETH
from .meta_ifd.model import MetaIFD

# Transformers imports
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer
)

class RiskDetectionPipeline:
    def __init__(self, config):
        self.config = config
        
        # Base risk weights
        self.risk_weights = {
            'unverified_contract': 0.35,  # Increased from 0.3
            'mint_privileges': 0.25,      # Increased from 0.2
            'high_mint_count': 0.20,      # Increased from 0.15
            'unlocked_liquidity': 0.30,   # Increased from 0.2
            'honeypot_result': 0.45,      # Increased from 0.4
            'new_contract': 0.20          # Increased from 0.15
        }
        
        # Combination multipliers for correlated risks
        self.risk_combinations = {
            ('unverified_contract', 'mint_privileges'): 1.2,
            ('unlocked_liquidity', 'honeypot_result'): 1.3,
            ('new_contract', 'unverified_contract'): 1.15,
            ('mint_privileges', 'high_mint_count'): 1.25
        }
    
    def analyze_address(self, address_data: Dict, features_text: str) -> Tuple[float, str, List[str]]:
        """
        Analyze an Ethereum address for potential fraud using heuristic rules
        Returns:
            - risk_score: Float between 0 and 1
            - risk_tier: String indicating risk level
            - explanation: List of explanation strings
        """
        features = address_data['features']
        risk_factors = []
        
        if features['is_contract']:
            # Collect all applicable risk factors
            if not features['verified_contract']:
                risk_factors.append(('unverified_contract', self.risk_weights['unverified_contract']))
            if features['has_mint_privileges']:
                risk_factors.append(('mint_privileges', self.risk_weights['mint_privileges']))
            if features['mint_event_count'] > 10:
                risk_factors.append(('high_mint_count', self.risk_weights['high_mint_count']))
            if not features['lp_locked']:
                risk_factors.append(('unlocked_liquidity', self.risk_weights['unlocked_liquidity']))
            if features['honeypot_result']:
                risk_factors.append(('honeypot_detected', self.risk_weights['honeypot_result']))
            if features['contract_age_days'] < 7:
                risk_factors.append(('new_contract', self.risk_weights['new_contract']))
            
            # Apply combination multipliers
            risk_score = 0
            applied_combinations = set()
            
            # First pass: calculate base risk score
            for factor, weight in risk_factors:
                risk_score += weight
            
            # Second pass: apply combination multipliers
            for i, (factor1, _) in enumerate(risk_factors):
                for j, (factor2, _) in enumerate(risk_factors[i+1:], i+1):
                    combo = tuple(sorted([factor1, factor2]))
                    if combo in self.risk_combinations and combo not in applied_combinations:
                        risk_score *= self.risk_combinations[combo]
                        applied_combinations.add(combo)
            
            # Normalize risk score
            risk_score = min(1.0, risk_score)
        else:
            risk_score = 0.0
            risk_factors = []
        
        # Get risk tier
        risk_tier = self._get_risk_tier(risk_score)
        
        # Generate explanation
        explanation = self._generate_explanation(
            risk_factors,
            risk_score,
            risk_tier,
            features_text
        )
        
        return risk_score, risk_tier, explanation
    
    def _get_risk_tier(self, score: float) -> str:
        """Map risk score to risk tier"""
        if score <= 0.3:
            return "Safe"
        elif score <= 0.7:
            return "Moderate Risk"
        else:
            return "High Risk"
    
    def _generate_explanation(
        self, 
        risk_factors: List[Tuple[str, float]], 
        risk_score: float, 
        risk_tier: str,
        features_text: str
    ) -> List[str]:
        """Generate explanation using predefined templates"""
        risk_explanations = {
            'unverified_contract': 'The contract source code is not verified on Etherscan, making it difficult to audit its functionality.',
            'mint_privileges': 'The contract owner has the ability to mint new tokens, which could lead to token supply manipulation.',
            'high_mint_count': 'There have been multiple token minting events, indicating potential supply inflation.',
            'unlocked_liquidity': 'The liquidity is not locked, allowing for potential rug pulls or token dumps.',
            'honeypot_detected': 'The contract exhibits characteristics of a honeypot, which may prevent token selling.',
            'new_contract': 'This is a newly deployed contract with limited history and community trust.'
        }
        
        explanations = []
        
        # Add overview
        explanations.append(f"Analysis Overview: {features_text}")
        
        # Add risk assessment
        explanations.append(f"Risk Assessment: This address has been classified as {risk_tier} with a risk score of {risk_score:.2f}")
        
        # Add risk factors
        if risk_factors:
            explanations.append("Detected Risk Factors:")
            for factor, score in risk_factors:
                explanations.append(f"- {risk_explanations[factor]} (Impact: {score:.2f})")
            
            # Add combination effects if any were applied
            applied_combos = []
            for i, (factor1, _) in enumerate(risk_factors):
                for j, (factor2, _) in enumerate(risk_factors[i+1:], i+1):
                    combo = tuple(sorted([factor1, factor2]))
                    if combo in self.risk_combinations:
                        applied_combos.append(
                            f"- Combined impact of {factor1} and {factor2} increases overall risk by " +
                            f"{(self.risk_combinations[combo] - 1) * 100:.0f}%"
                        )
            
            if applied_combos:
                explanations.append("\nRisk Factor Combinations:")
                explanations.extend(applied_combos)
        else:
            explanations.append("No significant risk factors were detected.")
        
        # Add recommendation
        if risk_tier == "High Risk":
            explanations.append("Recommendation: Exercise extreme caution when interacting with this address. Consider avoiding transactions unless you fully understand the risks.")
        elif risk_tier == "Moderate Risk":
            explanations.append("Recommendation: Proceed with caution and conduct thorough due diligence before any significant interactions.")
        else:
            explanations.append("Recommendation: While no major risks were detected, always follow standard security practices when conducting transactions.")
        
        return explanations 