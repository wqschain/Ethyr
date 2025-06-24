import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, SAGEConv, global_mean_pool
from typing import List, Dict, Tuple, Optional
import numpy as np

class TransactionEncoder(nn.Module):
    """Encodes Ethereum transactions into semantic embeddings"""
    def __init__(self, vocab_size: int, hidden_dim: int, num_heads: int = 8):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Transaction field embeddings
        self.address_embedding = nn.Embedding(vocab_size, hidden_dim)
        self.value_embedding = nn.Linear(1, hidden_dim)
        self.gas_embedding = nn.Linear(1, hidden_dim)
        
        # Multi-head attention for transaction sequence
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads)
        
        # Final transaction encoder
        self.encoder = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, hidden_dim)
        )
        
    def encode_transaction(self, tx: Dict) -> torch.Tensor:
        """Encode a single transaction into a fixed-size vector"""
        # Encode addresses (from/to)
        from_addr = self.address_embedding(tx['from_idx'])
        to_addr = self.address_embedding(tx['to_idx'])
        
        # Encode numerical values
        value = self.value_embedding(tx['value'].unsqueeze(-1))
        gas = self.gas_embedding(tx['gas'].unsqueeze(-1))
        
        # Combine all features
        combined = torch.cat([
            from_addr,
            to_addr,
            value + gas  # Combine transaction properties
        ], dim=-1)
        
        return self.encoder(combined)
    
    def forward(self, transactions: List[Dict]) -> torch.Tensor:
        """Encode a sequence of transactions with attention"""
        # Encode each transaction
        tx_embeddings = torch.stack([
            self.encode_transaction(tx) for tx in transactions
        ])
        
        # Apply attention over the sequence
        attended, _ = self.attention(
            tx_embeddings.unsqueeze(0),
            tx_embeddings.unsqueeze(0),
            tx_embeddings.unsqueeze(0)
        )
        
        return attended.squeeze(0)

class GraphEncoder(nn.Module):
    """Encodes the transaction graph structure using GNNs"""
    def __init__(self, hidden_dim: int):
        super().__init__()
        
        # Graph convolution layers
        self.conv1 = GCNConv(hidden_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        
        # GraphSAGE layer for neighborhood aggregation
        self.sage = SAGEConv(hidden_dim, hidden_dim)
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, batch=None) -> torch.Tensor:
        """Process the transaction graph"""
        # Initial graph convolutions
        x = torch.relu(self.conv1(x, edge_index))
        x = torch.relu(self.conv2(x, edge_index))
        
        # Neighborhood aggregation
        x = self.sage(x, edge_index)
        
        # Global pooling if batch information is provided
        if batch is not None:
            return global_mean_pool(x, batch)
        return x

class TLMG4ETH(nn.Module):
    """Transaction Language Model + Graph Neural Network for Ethereum"""
    def __init__(self, config):
        super().__init__()
        
        self.hidden_dim = config.hidden_dim
        
        # Transaction sequence encoder
        self.tx_encoder = TransactionEncoder(
            vocab_size=config.num_features,
            hidden_dim=config.hidden_dim,
            num_heads=config.num_heads
        )
        
        # Graph structure encoder
        self.graph_encoder = GraphEncoder(hidden_dim=config.hidden_dim)
        
        # Final classification layers
        self.classifier = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(config.hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, data) -> Tuple[torch.Tensor, Dict]:
        """
        Forward pass through the model
        Returns:
            - risk_score: Probability of fraudulent activity
            - attention_weights: Dictionary containing attention weights for interpretability
        """
        # Process transaction sequence
        tx_features = self.tx_encoder(data.transactions)
        
        # Process graph structure
        graph_features = self.graph_encoder(
            data.x,
            data.edge_index,
            getattr(data, 'batch', None)
        )
        
        # Combine features
        combined = torch.cat([
            tx_features.mean(dim=0),  # Average transaction features
            graph_features.mean(dim=0) if graph_features.dim() > 1 else graph_features
        ])
        
        # Get risk score
        risk_score = self.classifier(combined)
        
        return risk_score, {
            'transaction_attention': self.tx_encoder.attention._attn_weights,
            'graph_attention': self.graph_encoder.sage.attention_weights
        }
    
    def explain_prediction(self, data) -> Dict:
        """Generate explanations for the model's prediction"""
        self.eval()
        with torch.no_grad():
            risk_score, attention_weights = self.forward(data)
            
            # Get significant transactions based on attention
            tx_attention = attention_weights['transaction_attention']
            significant_tx = []
            if tx_attention is not None:
                tx_scores = tx_attention.mean(dim=1)
                for i, score in enumerate(tx_scores):
                    if score > 0.5:  # Threshold for significance
                        tx = data.transactions[i]
                        significant_tx.append({
                            'from': tx['from'],
                            'to': tx['to'],
                            'value': tx['value'],
                            'attention_score': score.item()
                        })
            
            # Get significant graph patterns
            graph_attention = attention_weights['graph_attention']
            significant_edges = []
            if graph_attention is not None:
                edge_scores = graph_attention.max(dim=-1).values
                for i, score in enumerate(edge_scores):
                    if score > 0.5:  # Threshold for significance
                        edge = (data.edge_index[0][i], data.edge_index[1][i])
                        significant_edges.append({
                            'from_node': edge[0].item(),
                            'to_node': edge[1].item(),
                            'attention_score': score.item()
                        })
            
            return {
                'risk_score': risk_score.item(),
                'significant_transactions': significant_tx,
                'significant_patterns': significant_edges
            } 