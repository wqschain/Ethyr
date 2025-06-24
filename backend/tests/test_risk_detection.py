import unittest
import sys
from pathlib import Path
import os

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from models.risk_detection_pipeline import RiskDetectionPipeline
from config import Config

class TestRiskDetectionPipeline(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config = Config()
        self.pipeline = RiskDetectionPipeline(self.config)
        
    def test_safe_contract(self):
        """Test a safe contract with no risk factors."""
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': True,
                'has_mint_privileges': False,
                'mint_event_count': 0,
                'lp_locked': True,
                'honeypot_result': False,
                'contract_age_days': 365
            }
        }
        features_text = "Contract is verified, has no mint privileges, and liquidity is locked."
        
        risk_score, risk_tier, explanation = self.pipeline.analyze_address(address_data, features_text)
        
        self.assertLessEqual(risk_score, 0.3)
        self.assertEqual(risk_tier, "Safe")
        self.assertIn("No significant risk factors were detected", explanation[-2])
        
    def test_high_risk_contract(self):
        """Test a high-risk contract with multiple risk factors."""
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': False,
                'has_mint_privileges': True,
                'mint_event_count': 15,
                'lp_locked': False,
                'honeypot_result': True,
                'contract_age_days': 2
            }
        }
        features_text = "Unverified contract with mint privileges and unlocked liquidity."
        
        risk_score, risk_tier, explanation = self.pipeline.analyze_address(address_data, features_text)
        
        self.assertGreaterEqual(risk_score, 0.7)
        self.assertEqual(risk_tier, "High Risk")
        self.assertIn("Exercise extreme caution", explanation[-1])
        
    def test_moderate_risk_contract(self):
        """Test a moderate-risk contract with some risk factors."""
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': True,
                'has_mint_privileges': True,
                'mint_event_count': 5,
                'lp_locked': False,
                'honeypot_result': False,
                'contract_age_days': 30
            }
        }
        features_text = "Verified contract but has mint privileges and unlocked liquidity."
        
        risk_score, risk_tier, explanation = self.pipeline.analyze_address(address_data, features_text)
        
        self.assertGreater(risk_score, 0.3)
        self.assertLess(risk_score, 0.7)
        self.assertEqual(risk_tier, "Moderate Risk")
        self.assertIn("Proceed with caution", explanation[-1])
        
    def test_non_contract_address(self):
        """Test a regular EOA (Externally Owned Account)."""
        address_data = {
            'features': {
                'is_contract': False,
                'verified_contract': False,
                'has_mint_privileges': False,
                'mint_event_count': 0,
                'lp_locked': False,
                'honeypot_result': False,
                'contract_age_days': 0
            }
        }
        features_text = "Regular externally owned account (EOA)."
        
        risk_score, risk_tier, explanation = self.pipeline.analyze_address(address_data, features_text)
        
        self.assertEqual(risk_score, 0.0)
        self.assertEqual(risk_tier, "Safe")
        
    def test_risk_factors_impact(self):
        """Test the impact of individual risk factors."""
        base_features = {
            'is_contract': True,
            'verified_contract': True,
            'has_mint_privileges': False,
            'mint_event_count': 0,
            'lp_locked': True,
            'honeypot_result': False,
            'contract_age_days': 365
        }
        
        # Test unverified contract impact
        features = base_features.copy()
        features['verified_contract'] = False
        score1, _, _ = self.pipeline.analyze_address({'features': features}, "")
        
        # Reset and test mint privileges impact
        features = base_features.copy()
        features['has_mint_privileges'] = True
        score2, _, _ = self.pipeline.analyze_address({'features': features}, "")
        
        # Verify the relative impact
        self.assertGreater(score1, score2)  # Unverified contract should have higher impact
        
    def test_explanation_completeness(self):
        """Test that explanations include all relevant information."""
        address_data = {
            'features': {
                'is_contract': True,
                'verified_contract': False,
                'has_mint_privileges': True,
                'mint_event_count': 15,
                'lp_locked': False,
                'honeypot_result': True,
                'contract_age_days': 2
            }
        }
        features_text = "Test contract with multiple risk factors."
        
        _, _, explanation = self.pipeline.analyze_address(address_data, features_text)
        
        required_elements = [
            "Analysis Overview",
            "Risk Assessment",
            "Detected Risk Factors",
            "Recommendation"
        ]
        
        for element in required_elements:
            self.assertTrue(
                any(element in exp for exp in explanation),
                f"Missing {element} in explanation"
            )

if __name__ == '__main__':
    unittest.main() 