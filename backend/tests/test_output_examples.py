import unittest
import sys
from pathlib import Path
import json
from pprint import pformat

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from models.risk_detection_pipeline import RiskDetectionPipeline
from config import Config

class TestOutputExamples(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.pipeline = RiskDetectionPipeline(self.config)
    
    def display_analysis(self, address_data, features_text):
        """Helper method to format and display analysis results"""
        risk_score, risk_tier, explanation = self.pipeline.analyze_address(
            address_data,
            features_text
        )
        
        output = {
            "risk_assessment": {
                "score": round(risk_score, 3),
                "tier": risk_tier,
            },
            "detailed_analysis": explanation,
        }
        
        return output
    
    def test_safe_contract_output(self):
        """Example output for a safe contract"""
        print("\n=== SAFE CONTRACT EXAMPLE ===")
        
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': True,
                'has_mint_privileges': False,
                'mint_event_count': 2,
                'lp_locked': True,
                'honeypot_result': False,
                'contract_age_days': 180,
                'owner_address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
                'transfer_volume_24h': 1500000
            }
        }
        
        features_text = "Verified contract with locked liquidity, limited mint activity, and established history."
        
        output = self.display_analysis(address_data, features_text)
        print(json.dumps(output, indent=2))
        
        self.assertEqual(output["risk_assessment"]["tier"], "Safe")
        self.assertLess(output["risk_assessment"]["score"], 0.3)
    
    def test_moderate_risk_output(self):
        """Example output for a moderate risk contract"""
        print("\n=== MODERATE RISK CONTRACT EXAMPLE ===")
        
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': True,
                'has_mint_privileges': True,
                'mint_event_count': 8,
                'lp_locked': False,
                'honeypot_result': False,
                'contract_age_days': 15,
                'owner_address': '0x123d35Cc6634C0532925a3b844Bc454e4438f789',
                'transfer_volume_24h': 750000
            }
        }
        
        features_text = "Verified contract with mint privileges and unlocked liquidity, moderate transaction history."
        
        output = self.display_analysis(address_data, features_text)
        print(json.dumps(output, indent=2))
        
        self.assertEqual(output["risk_assessment"]["tier"], "Moderate Risk")
        self.assertGreater(output["risk_assessment"]["score"], 0.3)
        self.assertLess(output["risk_assessment"]["score"], 0.7)
    
    def test_high_risk_output(self):
        """Example output for a high risk contract"""
        print("\n=== HIGH RISK CONTRACT EXAMPLE ===")
        
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': False,
                'has_mint_privileges': True,
                'mint_event_count': 15,
                'lp_locked': False,
                'honeypot_result': True,
                'contract_age_days': 2,
                'owner_address': '0x999d35Cc6634C0532925a3b844Bc454e4438fabc',
                'transfer_volume_24h': 250000
            }
        }
        
        features_text = "Unverified new contract with honeypot characteristics, high mint activity, and unlocked liquidity."
        
        output = self.display_analysis(address_data, features_text)
        print(json.dumps(output, indent=2))
        
        self.assertEqual(output["risk_assessment"]["tier"], "High Risk")
        self.assertGreater(output["risk_assessment"]["score"], 0.7)
    
    def test_non_contract_output(self):
        """Example output for a regular EOA"""
        print("\n=== REGULAR EOA EXAMPLE ===")
        
        address_data = {
            'features': {
                'is_contract': False,
                'verified_contract': False,
                'has_mint_privileges': False,
                'mint_event_count': 0,
                'lp_locked': False,
                'honeypot_result': False,
                'contract_age_days': 0,
                'owner_address': None,
                'transfer_volume_24h': 50000
            }
        }
        
        features_text = "Regular externally owned account (EOA) with normal transaction patterns."
        
        output = self.display_analysis(address_data, features_text)
        print(json.dumps(output, indent=2))
        
        self.assertEqual(output["risk_assessment"]["tier"], "Safe")
        self.assertEqual(output["risk_assessment"]["score"], 0.0)

if __name__ == '__main__':
    unittest.main() 