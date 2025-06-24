import random
from typing import Dict, Optional

def generate_contract_features(
    is_contract: bool = True,
    verified: Optional[bool] = None,
    mint_privileges: Optional[bool] = None,
    mint_count: Optional[int] = None,
    lp_locked: Optional[bool] = None,
    honeypot: Optional[bool] = None,
    age_days: Optional[int] = None
) -> Dict:
    """
    Generate synthetic contract features for testing.
    Parameters can be explicitly set or will be randomly generated if None.
    """
    if not is_contract:
        return {
            'is_contract': False,
            'verified_contract': False,
            'has_mint_privileges': False,
            'mint_event_count': 0,
            'lp_locked': False,
            'honeypot_result': False,
            'contract_age_days': 0
        }
    
    return {
        'is_contract': True,
        'verified_contract': verified if verified is not None else random.choice([True, False]),
        'has_mint_privileges': mint_privileges if mint_privileges is not None else random.choice([True, False]),
        'mint_event_count': mint_count if mint_count is not None else random.randint(0, 20),
        'lp_locked': lp_locked if lp_locked is not None else random.choice([True, False]),
        'honeypot_result': honeypot if honeypot is not None else random.choice([True, False]),
        'contract_age_days': age_days if age_days is not None else random.randint(1, 365)
    }

def generate_random_addresses(num_addresses: int = 10) -> list:
    """Generate a list of random test addresses with varying risk profiles."""
    addresses = []
    
    # Generate safe contracts (40%)
    safe_count = int(num_addresses * 0.4)
    for _ in range(safe_count):
        features = generate_contract_features(
            verified=True,
            mint_privileges=False,
            mint_count=random.randint(0, 5),
            lp_locked=True,
            honeypot=False,
            age_days=random.randint(30, 365)
        )
        addresses.append({
            'features': features,
            'expected_tier': 'Safe'
        })
    
    # Generate moderate risk contracts (35%)
    moderate_count = int(num_addresses * 0.35)
    for _ in range(moderate_count):
        # Create different combinations that lead to moderate risk
        if random.random() < 0.5:
            # Combination 1: Verified but with some risks
            features = generate_contract_features(
                verified=True,
                mint_privileges=True,
                mint_count=random.randint(5, 10),
                lp_locked=False,
                honeypot=False,
                age_days=random.randint(7, 30)
            )
        else:
            # Combination 2: Unverified but with safety measures
            features = generate_contract_features(
                verified=False,
                mint_privileges=False,
                mint_count=random.randint(0, 5),
                lp_locked=True,
                honeypot=False,
                age_days=random.randint(30, 60)
            )
        addresses.append({
            'features': features,
            'expected_tier': 'Moderate Risk'
        })
    
    # Generate high risk contracts (25%)
    remaining = num_addresses - len(addresses)
    for _ in range(remaining):
        # Create combinations that definitely lead to high risk
        if random.random() < 0.5:
            # Combination 1: Multiple severe risks
            features = generate_contract_features(
                verified=False,
                mint_privileges=True,
                mint_count=random.randint(10, 20),
                lp_locked=False,
                honeypot=True,
                age_days=random.randint(1, 7)
            )
        else:
            # Combination 2: Honeypot with other risks
            features = generate_contract_features(
                verified=False,
                mint_privileges=True,
                mint_count=random.randint(5, 15),
                lp_locked=False,
                honeypot=True,
                age_days=random.randint(1, 14)
            )
        addresses.append({
            'features': features,
            'expected_tier': 'High Risk'
        })
    
    random.shuffle(addresses)
    return addresses

def generate_test_batch(size: int = 100) -> Dict:
    """Generate a large batch of test data with known distributions."""
    addresses = generate_random_addresses(size)
    
    # Calculate expected statistics
    stats = {
        'Safe': len([a for a in addresses if a['expected_tier'] == 'Safe']),
        'Moderate Risk': len([a for a in addresses if a['expected_tier'] == 'Moderate Risk']),
        'High Risk': len([a for a in addresses if a['expected_tier'] == 'High Risk'])
    }
    
    return {
        'addresses': addresses,
        'statistics': stats
    } 