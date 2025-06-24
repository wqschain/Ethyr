import torch
import torch.nn as nn
from torch_geometric.nn import GATConv, MessagePassing
from torch.nn import Parameter
import torch.nn.functional as F

class MetaInteractionLayer(MessagePassing):
    def __init__(self, in_channels, out_channels):
        super(MetaInteractionLayer, self).__init__(aggr='add')
        self.lin = torch.nn.Linear(in_channels, out_channels)
        self.att = Parameter(torch.Tensor(1, out_channels))
        self.reset_parameters()
        
    def reset_parameters(self):
        nn.init.xavier_uniform_(self.att)
        
    def forward(self, x, edge_index, edge_type):
        # Compute attention coefficients
        x = self.lin(x)
        
        # Propagate messages
        return self.propagate(edge_index, x=x, edge_type=edge_type)
        
    def message(self, x_j, edge_type):
        # Compute message based on interaction type
        alpha = F.softmax(torch.matmul(x_j, self.att.t()), dim=1)
        return alpha * x_j

class MetaIFD(nn.Module):
    def __init__(self, num_features, hidden_dim=256, num_meta_relations=6):
        super(MetaIFD, self).__init__()
        
        self.num_meta_relations = num_meta_relations
        
        # Meta-interaction layers
        self.meta_layers = nn.ModuleList([
            MetaInteractionLayer(num_features, hidden_dim)
            for _ in range(num_meta_relations)
        ])
        
        # Graph attention layers
        self.gat1 = GATConv(hidden_dim, hidden_dim, heads=4)
        self.gat2 = GATConv(hidden_dim * 4, hidden_dim, heads=1)
        
        # Final prediction layers
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 2)  # Binary classification
        )
        
    def forward(self, x, edge_index, edge_type):
        # Process each meta-interaction type
        meta_features = []
        for i in range(self.num_meta_relations):
            mask = edge_type == i
            if mask.sum() > 0:
                meta_edge_index = edge_index[:, mask]
                meta_out = self.meta_layers[i](x, meta_edge_index, edge_type[mask])
                meta_features.append(meta_out)
        
        # Combine meta-interaction features
        if meta_features:
            x = torch.stack(meta_features).mean(dim=0)
        
        # Apply GAT layers
        x = F.relu(self.gat1(x, edge_index))
        x = F.relu(self.gat2(x, edge_index))
        
        # Final prediction
        return self.predictor(x)
    
    def get_risk_score(self, address_data):
        """Get risk score for an address"""
        self.eval()
        with torch.no_grad():
            risk_scores = self.forward(**address_data)
            probabilities = torch.softmax(risk_scores, dim=1)
            return probabilities[:, 1].item()  # Return probability of fraudulent class
            
    def extract_meta_interactions(self, transaction):
        """
        Extract meta-interaction type from transaction
        Types:
        0: CA->CA (call)
        1: EOA->CA (call)
        2: CA->CA (transfer)
        3: EOA->CA (transfer)
        4: CA->EOA (transfer)
        5: EOA->EOA (transfer)
        """
        from_is_contract = transaction['from_is_contract']
        to_is_contract = transaction['to_is_contract']
        is_call = transaction['is_call']
        
        if is_call:
            if from_is_contract and to_is_contract:
                return 0  # CA->CA call
            else:
                return 1  # EOA->CA call
        else:  # transfer
            if from_is_contract and to_is_contract:
                return 2  # CA->CA transfer
            elif not from_is_contract and to_is_contract:
                return 3  # EOA->CA transfer
            elif from_is_contract and not to_is_contract:
                return 4  # CA->EOA transfer
            else:
                return 5  # EOA->EOA transfer 