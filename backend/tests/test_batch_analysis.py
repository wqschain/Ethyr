import unittest
import sys
from pathlib import Path
import os

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from models.risk_detection_pipeline import RiskDetectionPipeline
from config import Config
from tests.test_utils import generate_test_batch

class TestBatchAnalysis(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config = Config()
        self.pipeline = RiskDetectionPipeline(self.config)
        
    def test_batch_processing(self):
        """Test processing a batch of addresses."""
        batch_size = 100
        test_data = generate_test_batch(batch_size)
        addresses = test_data['addresses']
        expected_stats = test_data['statistics']
        
        results = {
            'Safe': 0,
            'Moderate Risk': 0,
            'High Risk': 0
        }
        
        # Process each address
        for address in addresses:
            features_text = f"Test address with expected tier: {address['expected_tier']}"
            _, risk_tier, _ = self.pipeline.analyze_address(
                {'features': address['features']}, 
                features_text
            )
            results[risk_tier] += 1
        
        # Verify distribution is roughly as expected
        margin = batch_size * 0.15  # Allow 15% margin of error
        for tier in expected_stats:
            self.assertAlmostEqual(
                results[tier],
                expected_stats[tier],
                delta=margin,
                msg=f"Distribution for {tier} significantly different than expected"
            )
    
    def test_risk_score_ranges(self):
        """Test that risk scores fall within expected ranges for each tier."""
        test_data = generate_test_batch(50)
        
        for address in test_data['addresses']:
            risk_score, risk_tier, _ = self.pipeline.analyze_address(
                {'features': address['features']},
                "Test address"
            )
            
            # Verify score ranges
            if risk_tier == "Safe":
                self.assertLessEqual(risk_score, 0.3)
            elif risk_tier == "Moderate Risk":
                self.assertGreater(risk_score, 0.3)
                self.assertLessEqual(risk_score, 0.7)
            else:  # High Risk
                self.assertGreater(risk_score, 0.7)
    
    def test_consistency(self):
        """Test that the same input always produces the same output."""
        test_cases = generate_test_batch(10)['addresses']
        
        for address in test_cases:
            # First analysis
            score1, tier1, exp1 = self.pipeline.analyze_address(
                {'features': address['features']},
                "Test address"
            )
            
            # Second analysis
            score2, tier2, exp2 = self.pipeline.analyze_address(
                {'features': address['features']},
                "Test address"
            )
            
            # Verify results are identical
            self.assertEqual(score1, score2)
            self.assertEqual(tier1, tier2)
            self.assertEqual(exp1, exp2)
    
    def test_risk_factor_combinations(self):
        """Test various combinations of risk factors."""
        base_features = {
            'is_contract': True,
            'verified_contract': True,
            'has_mint_privileges': False,
            'mint_event_count': 0,
            'lp_locked': True,
            'honeypot_result': False,
            'contract_age_days': 365
        }
        
        # Test combinations of risk factors
        risk_factors = [
            'verified_contract',
            'has_mint_privileges',
            'lp_locked',
            'honeypot_result'
        ]
        
        previous_score = 0
        for i in range(len(risk_factors)):
            features = base_features.copy()
            # Add risk factors one by one
            for j in range(i + 1):
                if risk_factors[j] in ['verified_contract', 'lp_locked']:
                    features[risk_factors[j]] = False
                else:
                    features[risk_factors[j]] = True
            
            score, _, _ = self.pipeline.analyze_address({'features': features}, "")
            
            # Verify that more risk factors lead to higher risk scores
            self.assertGreater(score, previous_score)
            previous_score = score

if __name__ == '__main__':
    unittest.main() 